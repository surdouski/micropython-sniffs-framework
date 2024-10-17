from msf.utils.singleton import get_sniffs, singleton
from msf import MQTT_SENSORS_TOPIC


# class InvalidSensorConstructorArgs(Exception):
#     ...


class RemoteSensor:
    """Use this when defining a sensor foreign to the device."""
    @property
    def value(self):
        return self._value

    # def __init__(self, name: str = "", topic: str = ""):
    def __init__(self, name: str = ""):
        # if not (name or topic):
        #     raise InvalidSensorConstructorArgs("Must provide either name or topic.")
        # if name and topic:
        #     raise InvalidSensorConstructorArgs("Provided both name and topic, but must only provide one.")
        # if name:
        #     self.topic = MQTT_SENSORS_TOPIC + "/" + name
        # else:
        #     self.topic = topic
        # sniffs = get_sniffs()
        # sniffs.router.register(self.topic + "/value", lambda message: update_func(self, message))
        # @sniffs.route(self.topic + "/value")
        # async def update_func(message):
        #     # TODO: In future iterations, lets make a protocol for this message so that we can
        #     #   store more info inside of it. For now, we can just interpret the raw value at /value
        #     #   as the value.
        #     self._value = message
        #     self._on_update(self._value)

        self.topic = MQTT_SENSORS_TOPIC + "/" + name
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

    # def __init__(self, name: str = "", topic: str = "", value = None):
    def __init__(self, name: str = "", value = None):
        # if not (name or topic):
        #     raise InvalidSensorConstructorArgs("Must provide either name or topic.")
        # if name and topic:
        #     raise InvalidSensorConstructorArgs("Provided both name and topic, but must only provide one.")
        # if name:
        #     self.topic = MQTT_SENSORS_TOPIC + "/" + name
        # else:
        #     self.topic = topic

        self.topic = MQTT_SENSORS_TOPIC + "/" + name
        self._value =  value
        LocalSensorsRegistry()[name] = self

    async def update(self, new_value):
        self._value = new_value
        sniffs = get_sniffs()
        await sniffs.client.publish(f"{self.topic}/value", str(new_value))

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
