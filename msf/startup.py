from msf.sensor import RemoteSensorsRegistry

if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.getcwd())


from msf.utils.rtc import set_rtc
from msf.device import DevicesRegistry
from msf import MQTT_DEVICES_TOPIC, MQTT_AS_CONFIG_PATH, MQTT_SENSORS_TOPIC

from mpstore import load_store
from msf.utils.singleton import SniffsSingleton
from mqtt_as import config, MQTTClient

sniffs = SniffsSingleton()
devices = DevicesRegistry()
remote_sensors = RemoteSensorsRegistry()

@sniffs.route(MQTT_DEVICES_TOPIC + "/<device>/<setting>/value")
async def update_devices(device, setting, message):
    try:
        devices.update_device_setting(device, setting, message)
    except KeyError:
        pass  # TODO: Remove this when dynamic routing is available.
    except Exception as exception:
        # don't allow crashes from the update_devices call, just log it
        print(exception)  # TODO: Create/find a better logging solution.
        pass


@sniffs.route(MQTT_SENSORS_TOPIC + "/<sensor>/value")
async def update_remote_sensors(sensor, message):
    try:
        remote_sensors.update_remote_sensor(sensor, message)
    except KeyError:
        pass  # TODO: Remove this when dynamic routing is available.
    except Exception as exception:
        # don't allow crashes from the update_devices call, just log it
        print(exception)  # TODO: Create/find a better logging solution.
        pass


async def startup():
    mqtt_as_config = load_store(str(MQTT_AS_CONFIG_PATH))
    for key, val in mqtt_as_config.items():
        config[key] = val
    mqtt_client = MQTTClient(config)
    async def _on_connect():  # don't want to think about async lambda syntax atm
        await devices.on_mqtt_connect(mqtt_client)
    sniffs.on_connect = _on_connect
    await sniffs.bind(mqtt_client)
    await sniffs.client.connect()
    set_rtc()
