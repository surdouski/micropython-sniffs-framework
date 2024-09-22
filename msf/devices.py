import os
import asyncio

from mpstore import load_store, read_store, write_store

# from common.singleton import singleton
# from common.singleton import LocationSingleton, MQTTClientSingleton


class ValidationError(Exception):
    ...


class DeviceSettingsValidationError(Exception):
    ...


class ValidationMixin:
    _is_valid = None

    @property
    def is_valid(self) -> bool:
        if self._is_valid is None:
            self.validate()
        return self._is_valid

    def validate(self) -> bool:
        ...


def require_valid(func):
    def wrapper(self, *args, **kwargs):
        if not self.is_valid:
            raise ValidationError("Object requires is_valid to be True, but was False.")
        return func(self, *args, **kwargs)

    return wrapper


class Setting(ValidationMixin):
    accepted_string_types = ("str", "int", "float")

    @property
    @require_valid
    def value(self) -> str | int | float:
        return self._value

    @value.setter
    def value(self, new_value: str | int | float):
        try:
            self._value = self._type(new_value)
        except ValueError:
            raise DeviceSettingsValidationError(
                f"Cannot convert value '{new_value}' to type '{self._type}'."
            )
        write_store(f"{self.name}.value", str(self._value), self.file_path)

    @property
    @require_valid
    def type(self) -> type:
        return self._type

    def __init__(
        self,
        name: str,
        file_path: str,
        string_value: str,
        string_type: str,
        description: str,
    ):
        self.name = name
        self.file_path = file_path
        self.string_value = string_value
        self.string_type = string_type
        self.description = description

        self._value: str | int | float | None = None
        self._type: type | None = None

    def validate(self) -> bool:
        if not self.string_value:
            raise DeviceSettingsValidationError(
                f"Setting '{self.name}' requires 'value' to be defined."
            )
        if not self.string_type:
            raise DeviceSettingsValidationError(
                f"Setting '{self.name}' requires 'type' to be defined. (str/int/float)"
            )
        if not self.description:
            raise DeviceSettingsValidationError(
                f"Setting '{self.name}' requires 'description' to be defined."
            )
        if "." in self.name:
            raise DeviceSettingsValidationError(
                f"Setting '{self.name}' contains invalid character '.'."
            )

        if self.string_type not in self.accepted_string_types:
            raise DeviceSettingsValidationError(
                f"'Setting '{self.name}' with type '{self.string_type}' is not a valid option. Valid options are: {self.accepted_string_types}."
            )

        if self.string_type == "str":
            self._type = str
        elif self.string_type == "int":
            self._type = int
        elif self.string_type == "float":
            self._type = float

        try:
            self._value = self._type(self.string_value)
        except ValueError:
            raise DeviceSettingsValidationError(
                f"Setting '{self.name}' with value '{self.string_value}' is not a valid type '{self.string_type}'."
            )

        self._is_valid = True
        return True

    def __repr__(self):
        if not self._is_valid:
            return f"UnvalidatedSetting(name={self.name})"
        return f"Setting(name={self.name}, file_path={self.file_path}, value={self._value}, type={self._type})"


class Settings:
    def __init__(self):
        self.settings: dict[str, Setting] = {}

    def __getitem__(self, key: str) -> Setting:
        return self.settings[key]

    def __setitem__(self, key: str, value: any):
        self.settings[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.settings

    def __repr__(self):
        return f"Settings({self.settings})"


class Device:
    def __init__(self, name: str, file_path: str):
        self.name = name
        self.file_path = file_path
        self.settings = Settings()

    def __repr__(self):
        return f"Device(name={self.name}, file_path={self.file_path}, settings={self.settings})"


# @singleton
class DevicesRegistry:
    def __getitem__(self, key: str) -> Device:
        return self.devices[key]

    def __setitem__(self, key: str, value: Device):
        self.devices[key] = value

    def __repr__(self) -> str:
        return f"Devices({self.devices})"

    def __contains__(self, key: str) -> bool:
        return key in self.devices

    def __init__(self):
        self.devices: dict[str, Device] = {}
        self.devices_loaded = False

    def load_devices(self, devices_directory: str):
        """Each device setting requires a value, type, and description. These are
        designated in json with a typical nested json object format. Note
        that _all_ values must be strings, which are then cast to a python object
        based on the type.

        For example:
        ```json
        {
          "duty_cycle": {
            "value": "0.3",
            "type": "float",  # str, int, float
            "description": "Specifies the fraction of time the device is in an active or operational state during a complete cycle. A value of 0.3 means the device is active 30% of the time."
          }
        }
        ```
        """
        if self.devices_loaded:
            return

        for filename in os.listdir(devices_directory):
            if filename.endswith(".json"):
                file_path = f"{devices_directory}/{filename}"
                json_device_settings_dict = load_store(file_path)
                device_name = filename[:-5]  # Remove .json extension

                device = Device(device_name, file_path)
                self.devices[device_name] = device

                for setting_name, setting_dict in json_device_settings_dict.items():
                    if not setting_dict or not isinstance(setting_dict, dict):
                        raise DeviceSettingsValidationError(
                            f"Setting '{setting_name}' must be a json dict with defined keys for value, type, and description."
                        )

                    value = setting_dict.get("value")
                    _type = setting_dict.get("type")
                    description = setting_dict.get("description")
                    setting = Setting(
                        setting_name, file_path, value, _type, description
                    )
                    setting.validate()
                    device.settings[setting_name] = setting
        self.devices_loaded = True
        # await self._publish_device(device_name)

    # async def _publish_device(self, device_name: str):
    #     location = LocationSingleton()
    #     client = MQTTClientSingleton()
    #     await asyncio.gather(
    #         client.publish(
    #             f"{location}/devices/{device_name}/{setting.name}",
    #             setting.value,
    #             retain=True,
    #         )
    #         for setting in self.devices["device_name"].values()
    #     )

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

        try:
            setting.value = setting.type(setting_value)
        except ValueError:
            raise DeviceSettingsValidationError(
                f"Cannot convert setting '{setting_value}' to type '{setting.type}'."
            )
