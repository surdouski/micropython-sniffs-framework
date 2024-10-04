if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.getcwd())


from msf.device import DevicesRegistry
from msf import MQTT_DEVICES_TOPIC, MQTT_AS_CONFIG_PATH

from mpstore import load_store
from usniffs import Sniffs
from mqtt_as import config, MQTTClient

sniffs = Sniffs()
devices = DevicesRegistry()

@sniffs.route(MQTT_DEVICES_TOPIC + "/<device>/<setting>/value")
async def update_devices(device, setting, message):
    try:
        devices.update_device_setting(device, setting, message)
    except Exception as exception:
        # don't allow crashes from the update_devices call, just log it
        print(exception)  # TODO: create/find a better logging solution
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
