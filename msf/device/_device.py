import asyncio
from pathlib import Path
from msf import DEVICES_SETTINGS_PATH, MQTT_DEVICES_TOPIC

from mpstore import write_store, read_store
from msf.utils.singleton import singleton


class ValidationError(Exception):
    ...


class DeviceSettingsValidationError(Exception):
    ...


class DuplicateDeviceNameException(Exception):
    pass


class InvalidDeviceNameException(Exception):
    pass


class DuplicateDeviceSettingNameException(Exception):
    pass


class Setting:
    supported_types = (str, int, float)

    @property
    def value(self):  # -> str | int | float
        return self._value

    @property
    def type(self) -> type:
        return self._type

    @property
    def description(self) -> str:
        if self._description is None:
            return f"Description for {self.name} with value of type {self.type.__name__}."

    @property
    def file_path(self) -> Path:
        return self._file_path

    def __init__(
        self,
        name: str,
        value: any,
        description: str,
    ):
        if not type(value) in self.supported_types:
            raise DeviceSettingsValidationError(f"Setting '{name} required to be in: {self.supported_types}'")

        self.name = name

        self._description = description
        self._type = type(value)
        self._value = value
        self._file_path = None

    def set_path(self, file_path: Path):
        self._file_path = file_path

    def update(self, value):
        if not isinstance(value, self.type):
            try:
                value = self.type(value)
            except Exception:
                raise DeviceSettingsValidationError(
                    f"Was given setting value '{value}', but was not of expected type '{self.type.__name__}'."
                )

        if self._value != value:
            self._value = value
            self._on_update()

    def _on_update(self):
        pass

    def on_update(self):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(self.value)

            self._on_update = wrapper
            return wrapper

        return decorator


    def __repr__(self):
        return f"Setting(name={self.name}, value={self._value})"


class Settings:
    def __init__(self, settings_dict: dict[str, Setting]):
        self._dict = settings_dict

    def __getitem__(self, key: str) -> Setting:
        return self._dict[key]

    def __setitem__(self, key: str, value: any):
        self._dict[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._dict

    def __iter__(self):
        return iter(self._dict.values())

    def get(self, key: str):
        return self._dict.get(key)

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def keys(self):
        return self._dict.keys()

    def __repr__(self):
        return f"Settings({self._dict})"


class Device:
    name: str
    settings: Settings

    def __init__(self, device_name: str, settings: list[Setting]):
        if "." in device_name:
            raise InvalidDeviceNameException(f"Attempted to create a new device with name {device_name}, but character '.' is not allowed in device name.")
        if DevicesRegistry().get(device_name):
            raise DuplicateDeviceNameException(f"Attempted to create a new device with name {device_name}, but a device with that name already exists.")
        self.name = device_name

        settings_map: dict[str, Setting] = {}
        for setting in settings:
            if settings_map.get(setting.name):
                raise DuplicateDeviceSettingNameException(f"Attempted to create a new device setting with name {setting.name}, but a device setting with that name already exists.")

            _store_setting = read_store(f"{device_name}.{setting.name}", str(DEVICES_SETTINGS_PATH))
            if not _store_setting:
                # If it does not exist, we want to write an initial setting
                setting_dict = {
                    "value": str(setting.value),
                    "type": setting.type.__name__,
                    "description": setting.description
                }
                write_store(f"{device_name}.{setting.name}", setting_dict, str(DEVICES_SETTINGS_PATH))
            else:
                # If it does exist, we want to update the setting object's value from the current JSON setting
                _value = _store_setting["value"]
                try:
                    setting._value = setting.type(_value)
                except ValueError:
                    raise DeviceSettingsValidationError(
                        f"Cannot convert setting value '{_value}' to type '{setting.type.__name__}'."
                    )

            settings_map[setting.name] = setting

        self.settings = Settings(settings_map)

        DevicesRegistry()[device_name] = self

    def _list_settings(self) -> list[Setting]:
        return [_setting for _setting in self.settings.values()]

    def __repr__(self):
        return f"Device(name={self.name}, settings={self._list_settings()})"


@singleton
class DevicesRegistry:
    devices: dict[str, Device]
    devices_loaded: bool
    device_settings_path: Path = DEVICES_SETTINGS_PATH  # For ease of access

    def __getitem__(self, key: str) -> Device:
        return self.devices[key]

    def __setitem__(self, key: str, value: Device):
        self.devices[key] = value

    def __repr__(self) -> str:
        return f"Devices({self.devices})"

    def __contains__(self, key: str) -> bool:
        return key in self.devices

    def get(self, device_name) -> Device:  # |  None
        if device_name in self:
            return self[device_name]
        return None

    def __init__(self):
        self.devices = {}
        self.devices_loaded = False

    def reset(self):
        self.devices = {}
        self.devices_loaded = False

    def update_device_setting(
        self, device_name: str, setting_name: str, setting_value: any
    ):
        if device_name not in self.devices:
            raise KeyError(f"Device '{device_name}' not found.")

        device = self.devices[device_name]
        if setting_name not in device.settings:
            raise KeyError(
                f"Setting '{setting_name}' not found for device '{device_name}'."
            )

        setting = device.settings[setting_name]
        setting.update(setting_value)
        write_store(f"{device_name}.{setting.name}.value", str(setting.value), str(DEVICES_SETTINGS_PATH))

    async def on_mqtt_connect(self, client):
        to_be_published = []
        for device in self.devices.values():
            for setting in device.settings:
                to_be_published.append(client.publish(f"{MQTT_DEVICES_TOPIC}/{device.name}/{setting.name}/description", str(setting.description), retain=True))
                to_be_published.append(client.publish(f"{MQTT_DEVICES_TOPIC}/{device.name}/{setting.name}/type", str(setting.type.__name__), retain=True))
                to_be_published.append(client.publish(f"{MQTT_DEVICES_TOPIC}/{device.name}/{setting.name}/value/reported", str(setting.value), retain=True))
        await asyncio.gather(*to_be_published)