import unittest
import sys
import os

sys.path.append(os.getcwd())

from settings import DEVICES_DIR
from mpstore import write_store, read_store
from msf.device import DevicesRegistry, DeviceSettingsValidationError

pump_path = f"{DEVICES_DIR}/water_pump.json"
no_type_path = f"{DEVICES_DIR}/no_type.json"
no_description_path = f"{DEVICES_DIR}/no_description.json"
no_value_path = f"{DEVICES_DIR}/no_value.json"
invalid_type_path = f"{DEVICES_DIR}/invalid_type.json"
parse_type_fail_path = f"{DEVICES_DIR}/parse_type_fail_path.json"


class DeviceTests(unittest.TestCase):
    def setUp(self):
        DevicesRegistry().reset()
        write_store("duty_cycle.value", "0.3", pump_path)
        write_store("duty_cycle.type", "float", pump_path)
        write_store(
            "duty_cycle.description",
            "Specifies the fraction of time the device is in an active or operational state during a complete cycle. A value of 0.3 means the device is active 30% of the time.",
            pump_path,
        )
        write_store("foo_setting.value", "5", pump_path)
        write_store("foo_setting.type", "int", pump_path)
        write_store("foo_setting.description", "Specifies the foo!", pump_path)
        write_store("bar_setting.value", "bar string", pump_path)
        write_store("bar_setting.type", "str", pump_path)
        write_store("bar_setting.description", "Specifies the bar!", pump_path)

    def test_load_devices__device_name(self):
        registry = DevicesRegistry()
        registry.load_devices()

        assert "water_pump" in registry

    def test_load_devices__setting_name(self):
        registry = DevicesRegistry()
        registry.load_devices()

        assert "duty_cycle" in registry["water_pump"].settings

    def test_load_devices__missing_value(self):
        registry = DevicesRegistry()
        write_store("missing_value_setting.type", "missing the value", no_value_path)
        write_store(
            "missing_value_setting.description", "missing the value", no_value_path
        )
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices()
        os.remove(no_value_path)

    def test_load_devices__missing_type(self):
        registry = DevicesRegistry()
        write_store("missing_type_setting.value", "missing the type", no_type_path)
        write_store(
            "missing_type_setting.description", "missing the type", no_type_path
        )
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices()
        os.remove(no_type_path)

    def test_load_devices__missing_description(self):
        registry = DevicesRegistry()
        write_store(
            "missing_description_setting.value",
            "missing the description",
            no_description_path,
        )
        write_store("missing_description_setting.type", "str", no_description_path)
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices()
        os.remove(no_description_path)

    def test_load_devices__invalid_period(self):
        registry = DevicesRegistry()
        write_store(
            "invalid_period.value", "missing the description", no_description_path
        )
        write_store("invalid_period.type", "str", no_description_path)
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices()
        os.remove(no_description_path)

    def test_load_devices__invalid_type(self):
        registry = DevicesRegistry()
        write_store("invalid_type.value", "invalid type", invalid_type_path)
        write_store("invalid_type.type", "3", invalid_type_path)
        write_store("invalid_type.description", "invalid type", invalid_type_path)
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices()
        os.remove(invalid_type_path)

    def test_load_devices__parse_type_fail(self):
        registry = DevicesRegistry()
        write_store(
            "parse_type_fail.value", "parse_type_fail value", parse_type_fail_path
        )
        write_store("parse_type_fail.type", "float", parse_type_fail_path)
        write_store(
            "parse_type_fail.description",
            "parse_type_fail description",
            parse_type_fail_path,
        )
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices()
        os.remove(parse_type_fail_path)

    def test_update_device_setting__basic(self):
        registry = DevicesRegistry()
        registry.load_devices()

        registry.update_device_setting("water_pump", "duty_cycle", 4.0)
        registry.update_device_setting("water_pump", "foo_setting", 4.0)
        registry.update_device_setting("water_pump", "bar_setting", 4.0)

        assert read_store("duty_cycle.value", pump_path) == "4.0"
        assert read_store("foo_setting.value", pump_path) == "4"
        assert read_store("bar_setting.value", pump_path) == "4.0"

    def test_update_device_setting__setting_dne(self):
        registry = DevicesRegistry()
        registry.load_devices()
        with self.assertRaises(KeyError):
            registry.update_device_setting("water_pump", "jury_duty", 4.0)

    def test_update_device_settings__device_dne(self):
        registry = DevicesRegistry()
        registry.load_devices()
        with self.assertRaises(KeyError):
            registry.update_device_setting("dne", "jury_duty", 4.0)

    def test_update_device_settings__invalid_type(self):
        registry = DevicesRegistry()
        registry.load_devices()
        with self.assertRaises(DeviceSettingsValidationError):
            registry.update_device_setting("water_pump", "duty_cycle", "abc")

    def test_update_device_settings__json_saves_as_string(self):
        registry = DevicesRegistry()
        registry.load_devices()
        registry.update_device_setting("water_pump", "duty_cycle", 4.0)
        duty_cycle_value = read_store("duty_cycle.value", pump_path)
        assert isinstance(duty_cycle_value, str)

    def test_update_device_settings__device_value_saves_as_type(self):
        registry = DevicesRegistry()
        registry.load_devices()
        registry.update_device_setting("water_pump", "duty_cycle", "4.0")
        assert isinstance(registry["water_pump"].settings["duty_cycle"].value, float)



unittest.main()
