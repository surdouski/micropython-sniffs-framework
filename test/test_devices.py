import unittest
import sys
import os

sys.path.append(os.getcwd())

from mpstore import load_store, write_store

from msf.settings import DEVICES_SETTINGS_PATH
from msf.device import (
    DevicesRegistry,
    DeviceSettingsValidationError,
    Device,
    Setting,
    InvalidDeviceNameException,
    DuplicateDeviceNameException,
    DuplicateDeviceSettingNameException,
)


class DeviceTests(unittest.TestCase):
    registry = DevicesRegistry()
    test_device: Device
    duty_cycle: Setting
    foo_setting: Setting
    bar_setting: Setting

    def setUp(self):
        self.registry.reset()
        self.duty_cycle = Setting(
            "duty_cycle",
            0.3,
            "Specifies the fraction of time the device is in an active or operational state during a complete cycle. A value of 0.3 means the device is active 30% of the time.",
        )
        self.foo_setting = Setting("foo_setting", 5, "Foo setting.")
        self.bar_setting = Setting("bar_setting", "bar string", "Bar Setting.")
        self.test_device = Device(
            "water_pump", [self.duty_cycle, self.foo_setting, self.bar_setting]
        )

    def test_created_device__in_registry(self):
        assert "water_pump" in self.registry

    def test_created_setting__in_device(self):
        assert "duty_cycle" in self.registry["water_pump"].settings

    def test_create_setting__type_not_supported(self):
        with self.assertRaises(DeviceSettingsValidationError):
            new_setting = Setting(
                name="foo", value=b"unsupported binary string", description="abc123"
            )

    def test_create_device__invalid_period_in_name(self):
        with self.assertRaises(InvalidDeviceNameException):
            new_device = Device("invalid.period", [])

    def test_create_device__invalid_duplicate_device_name(self):
        with self.assertRaises(DuplicateDeviceNameException):
            new_device = Device("water_pump", [])

    def test_create_device__duplicate_setting_name(self):
        with self.assertRaises(DuplicateDeviceSettingNameException):
            duplicate_setting = Setting("foo_setting", 10, "Duplicate Foo setting.")
            new_device = Device("new_device", [duplicate_setting, self.foo_setting])

    def test_update_device_setting(self):
        self.registry.update_device_setting("water_pump", "duty_cycle", 12.5)
        value = self.registry.get("water_pump").settings.get("duty_cycle").value
        assert value == 12.5, f"Expected: 12.5, Actual: {value}"

    def test_update_device_setting__invalid_setting_name(self):
        with self.assertRaises(KeyError):
            self.registry.update_device_setting("water_pump", "invalid_setting", 10)

    def test_update_device_setting__invalid_device_name(self):
        with self.assertRaises(KeyError):
            self.registry.update_device_setting(
                "non_existent_device", "foo_setting", 10
            )

    def test_update_device_setting__invalid_value_type(self):
        with self.assertRaises(DeviceSettingsValidationError):
            self.registry.update_device_setting(
                "water_pump", "foo_setting", "invalid_value"
            )

    def test_update_device_setting__castable_value_to_type(self):
        self.registry.update_device_setting("water_pump", "duty_cycle", "0.22")
        assert self.duty_cycle.value == 0.22, f"Expected: 0.22, Actual: {self.duty_cycle.value}"

    def test_store_invalid_value_conversion(self):
        with self.assertRaises(DeviceSettingsValidationError):
            invalid_setting = Setting(
                "invalid_setting", 99, "Invalid setting description."
            )
            # Attempting to convert string to a type it cannot handle
            invalid_device = Device("invalid_device", [invalid_setting])
            self.registry.update_device_setting(
                "invalid_device", "invalid_setting", "22.0"
            )

    def test_json_settings_saved_correctly(self):
        """
        This is the expected object dict from the JSON for this test method:
        {
          "water_pump": {
            "duty_cycle": {
              "value": "0.3",
              "type": "float",
              "description": "Specifies the fraction of time the device is in an active or operational state during a complete cycle."
            },
            "foo_setting": {
              "value": "5",
              "type": "int",
              "description": "Foo setting."
            },
            "bar_setting": {
              "value": "bar string",
              "type": "str",
              "description": "Bar Setting."
            }
          },
          "not_water_pump": {
            "another_setting": {
              "value": "5",
              "type": "int",
              "description": "Foo setting."
            },
            "abc123": {
              "value": "bar string",
              "type": "str",
              "description": "Bar Setting."
            }
          }
        }

        """
        another_setting = Setting("another_setting", 5, "Foo setting.")
        abc123 = Setting("abc123", "bar string", "Bar Setting.")
        test_device = Device(
            "not_water_pump", [another_setting, abc123]
        )
        load_settings = load_store(str(DEVICES_SETTINGS_PATH))

        _water_pump = load_settings.get("water_pump")
        _not_water_pump = load_settings.get("not_water_pump")
        assert _water_pump is not None
        assert _not_water_pump is not None

        _duty = _water_pump.get("duty_cycle")
        _foo_setting = _water_pump.get("foo_setting")
        _bar_setting = _water_pump.get("bar_setting")
        _another_setting = _not_water_pump.get("another_setting")
        _abc123 = _not_water_pump.get("abc123")
        assert _duty is not None
        assert _foo_setting is not None
        assert _bar_setting is not None
        assert _another_setting is not None
        assert _abc123 is not None

        assert _duty.get("value") == str(self.duty_cycle.value)
        assert _duty.get("type") == self.duty_cycle.type.__name__
        assert _duty.get("description") == self.duty_cycle.description

        assert _foo_setting.get("value") == str(self.foo_setting.value)
        assert _foo_setting.get("type") == self.foo_setting.type.__name__
        assert _foo_setting.get("description") == self.foo_setting.description

        assert _bar_setting.get("value") == str(self.bar_setting.value)
        assert _bar_setting.get("type") == self.bar_setting.type.__name__
        assert _bar_setting.get("description") == self.bar_setting.description

        assert _another_setting.get("value") == str(another_setting.value)
        assert _another_setting.get("type") == another_setting.type.__name__
        assert _another_setting.get("description") == another_setting.description

        assert _abc123.get("value") == str(abc123.value)
        assert _abc123.get("type") == abc123.type.__name__
        assert _abc123.get("description") == abc123.description

    def test_on_update_decorator(self):
        value_updated = 0

        @self.duty_cycle.on_update()
        def water_pump_change_duty(value):
            nonlocal value_updated
            value_updated = value

        self.registry.update_device_setting("water_pump", "duty_cycle", 2.25)

        assert value_updated == 2.25, f"Expected: 2.25, Actual: {value_updated}"

    def test_saved_state_overrides_setting_value(self):
        # create the saved state manually
        write_store("unique_device", {
            "another_setting": {
                "value": "6",
                "type": "int",
                "description": "Another setting."
            }
        }, str(DEVICES_SETTINGS_PATH))

        another_setting = Setting("another_setting", 5, "Another setting.")
        assert another_setting.value == 5
        Device("unique_device", [another_setting])
        assert another_setting.value == 6


unittest.main()
