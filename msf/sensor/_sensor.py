from msf.utils.singleton import get_sniffs, singleton
from msf import MQTT_SENSORS_TOPIC

# TODO: finish foreign sensor and create registries for both. possibly abstract the registry idea afterward.


class InvalidSensorConstructorArgs(Exception):
    ...


# Define update_func outside the class
async def update_func(remote_sensor, message):
    # Interpret the raw value from /value as the sensor value.
    remote_sensor._value = message
    remote_sensor._on_update(remote_sensor._value)


class RemoteSensor:
    """Use this when defining a sensor foreign to the device."""
    @property
    def value(self):
        return self._value

    def __init__(self, name: str = "", topic: str = ""):
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

    def __init__(self, name: str = "", topic: str = "", value = None):
        if not (name or topic):
            raise InvalidSensorConstructorArgs("Must provide either name or topic.")
        if name and topic:
            raise InvalidSensorConstructorArgs("Provided both name and topic, but must only provide one.")

        if name:
            self.topic = MQTT_SENSORS_TOPIC + "/" + name
        else:
            self.topic = topic
        self._value =  value

    async def update(self, new_value):
        self._value = new_value
        sniffs = get_sniffs()
        await sniffs.client.publish(f"{self.topic}/value", str(new_value))
