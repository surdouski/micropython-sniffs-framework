from msf.utils.singleton import get_sniffs, singleton
from msf import MQTT_SENSORS_TOPIC


class InvalidSensorConstructorArgs(Exception):
    ...


class RemoteSensor:
    """Use this when defining a sensor foreign to the device."""
    @property
    def value(self):
        return self._value

    def __init__(self, name: str, topic_override: str = ""):
        """If topic_override is provided, will override the default MQTT_SENSORS_TOPIC/sensor_name/value topic."""
        if topic_override:
            self.topic = topic_override
        else:
            self.topic = MQTT_SENSORS_TOPIC + "/" + name + "/value"

        sniffs = get_sniffs()
        @sniffs.route(self.topic)
        async def update_func(message):
            self._value = message
            self._on_update()

        self._value = None

        RemoteSensorsRegistry()[name] = self

    def update(self, value):
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


@singleton
class RemoteSensorsRegistry:
    remote_sensors: dict[str, RemoteSensor]

    def __getitem__(self, key: str) -> RemoteSensor:
        return self.remote_sensors[key]

    def __setitem__(self, key: str, value: RemoteSensor):
        self.remote_sensors[key] = value

    def __repr__(self) -> str:
        return f"RemoteSensors({self.remote_sensors})"

    def __contains__(self, key: str) -> bool:
        return key in self.remote_sensors

    def get(self, remote_sensor) -> RemoteSensor:  # |  None
        if remote_sensor in self:
            return self[remote_sensor]

    def __init__(self):
        self.remote_sensors = {}

    def reset(self):
        self.remote_sensors = {}

    def update_remote_sensor(self, sensor_name: str, sensor_value: any):
        if sensor_name not in self.remote_sensors:
            raise KeyError(f"RemoteSensor '{sensor_name}' not found.")

        remote_sensor = self.remote_sensors[sensor_name]
        remote_sensor.update(sensor_value)


class LocalSensor:
    """Use this when defining a sensor local to the device."""
    @property
    def value(self):
        return self._value

    def __init__(self, name: str, topic_override: str = ""):
        """If topic_override is provided, will override the default MQTT_SENSORS_TOPIC/sensor_name/value topic."""
        if topic_override:
            self.topic = topic_override
        else:
            self.topic = MQTT_SENSORS_TOPIC + "/" + name + "/value"

        self._value = None

        LocalSensorsRegistry()[name] = self

    async def update(self, new_value):
        self._value = new_value
        sniffs = get_sniffs()
        await sniffs.client.publish(f"{self.topic}", str(new_value))

@singleton
class LocalSensorsRegistry:
    local_sensors: dict[str, LocalSensor]

    def __getitem__(self, key: str) -> LocalSensor:
        return self.local_sensors[key]

    def __setitem__(self, key: str, value: LocalSensor):
        self.local_sensors[key] = value

    def __repr__(self) -> str:
        return f"LocalSensors({self.local_sensors})"

    def __contains__(self, key: str) -> bool:
        return key in self.local_sensors

    def get(self, local_sensor) -> LocalSensor:  # |  None
        if local_sensor in self:
            return self[local_sensor]

    def __init__(self):
        self.local_sensors = {}

    def reset(self):
        self.local_sensors = {}

    def update_local_sensor(self, sensor_name: str, sensor_value: any):
        if sensor_name not in self.local_sensors:
            raise KeyError(f"LocalSensor '{sensor_name}' not found.")

        local_sensor = self.local_sensors[sensor_name]
        local_sensor.update(sensor_value)
