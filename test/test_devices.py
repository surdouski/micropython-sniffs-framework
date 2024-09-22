import unittest
import sys
import os
sys.path.append(os.getcwd())

from mpstore import write_store, read_store
from msf.devices import DevicesRegistry, DeviceSettingsValidationError

devices_dir = "/devices"
pump_path = f"{devices_dir}/water_pump.json"
no_type_path = f"{devices_dir}/no_type.json"
no_description_path = f"{devices_dir}/no_description.json"

class DeviceTests(unittest.TestCase):
    def setUp(self):
        write_store("duty_cycle.value", "0.3", pump_path)
        write_store("duty_cycle.type", "float", pump_path)
        write_store("duty_cycle.description", "Specifies the fraction of time the device is in an active or operational state during a complete cycle. A value of 0.3 means the device is active 30% of the time.", pump_path)
        write_store("foo_setting.value", "5", pump_path)
        write_store("foo_setting.type", "int", pump_path)
        write_store("foo_setting.description", "Specifies the foo!", pump_path)
        write_store("bar_setting.value", "bar string", pump_path)
        write_store("bar_setting.type", "str", pump_path)
        write_store("bar_setting.description", "Specifies the bar!", pump_path)

    def test_load_devices__device_name(self):
        registry = DevicesRegistry()
        registry.load_devices(devices_dir)

        assert "water_pump" in registry

    def test_load_devices__missing_type(self):
        registry = DevicesRegistry()
        write_store("missing_type_setting.value", "missing the type", no_type_path)
        write_store("missing_type_setting.description", "missing the type", no_type_path)
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices(devices_dir)
        os.remove(no_type_path)

    def test_load_devices__missing_description(self):
        registry = DevicesRegistry()
        write_store("missing_description_setting.value", "missing the description",no_description_path)
        write_store("missing_description_setting.type", "str", no_description_path)
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices(devices_dir)
        os.remove(no_description_path)

    def test_load_devices__setting_invalid_period(self):
        registry = DevicesRegistry()
        write_store("missing_description_setting.value", "missing the description",no_description_path)
        write_store("missing_description_setting.type", "str", no_description_path)
        with self.assertRaises(DeviceSettingsValidationError):
            registry.load_devices(devices_dir)
        os.remove(no_description_path)

    def test_update_device_setting__basic(self):
        registry = DevicesRegistry()
        registry.load_devices(devices_dir)

        registry.update_device_setting("water_pump", "duty_cycle", 4.0)
        registry.update_device_setting("water_pump", "foo_setting", 4.0)
        registry.update_device_setting("water_pump", "bar_setting", 4.0)

        assert read_store("duty_cycle.value", pump_path) == "4.0"
        assert read_store("foo_setting.value", pump_path) == "4"
        assert read_store("bar_setting.value", pump_path) == "4.0"


    def test_update_device_setting__setting_dne(self):
        registry = DevicesRegistry()
        registry.load_devices(devices_dir)
        with self.assertRaises(KeyError):
            registry.update_device_setting("water_pump", "jury_duty", 4.0)

    def test_update_device_settings__setting_dne(self):
        registry = DevicesRegistry()
        registry.load_devices(devices_dir)
        with self.assertRaises(KeyError):
            registry.update_device_setting("water_pump", "jury_duty", 4.0)



unittest.main()