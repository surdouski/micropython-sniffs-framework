import unittest
import sys
import os

sys.path.append(os.getcwd())

from msf.sensor import (
    LocalSensorsRegistry,
    RemoteSensorsRegistry,
    LocalSensor,
    RemoteSensor,
)


class SensorTests(unittest.TestCase):
    local_sensors_registry = LocalSensorsRegistry()
    remote_sensors_registry = RemoteSensorsRegistry()

    def setUp(self):
        self.local_sensors_registry.reset()
        self.remote_sensors_registry.reset()


    def test_created_local_sensor__in_registry(self):
        LocalSensor(name="foo")
        assert "foo" in self.local_sensors_registry

    def test_created_remote_sensor__in_registry(self):
        RemoteSensor(name="foo")
        assert "foo" in self.remote_sensors_registry

    def test_remote_sensor_on_update_decorator(self):
        value_updated = 0
        remote_sensor = RemoteSensor(name="foo")

        @remote_sensor.on_update()
        def update_new_value(value):
            nonlocal value_updated
            value_updated = value

        self.remote_sensors_registry.update_remote_sensor("foo", 22)

        assert value_updated == 22, f"Expected: 22, Actual: {value_updated}"
        assert self.remote_sensors_registry.get("foo").value == 22, f"Expected: 22, Actual: {self.remote_sensors_registry.get('foo').value}"

    def test_remote_sensor_on_update_decorator_using_topic_override(self):
        value_updated = 0
        remote_sensor = RemoteSensor(name="foo", topic_override="abc123")

        @remote_sensor.on_update()
        def update_new_value(value):
            nonlocal value_updated
            value_updated = value

        self.remote_sensors_registry.update_remote_sensor("foo", 22)

        assert value_updated == 22, f"Expected: 22, Actual: {value_updated}"
        assert self.remote_sensors_registry.get("foo").value == 22, f"Expected: 22, Actual: {self.remote_sensors_registry.get('foo').value}"


unittest.main()
