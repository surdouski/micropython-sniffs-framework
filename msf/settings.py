# settings.py
# Similar to the new project directory, settings.py is used for identifying locations of
# different modules and files.
from pathlib import Path


DEVICES_SETTINGS_PATH = Path("/.settings") / "devices.json"

MQTT_AS_CONFIG_PATH = Path("/.config") / "mqtt_as.json"

# IMPORTANT: DO NOT start mqtt topic's with a "/"
MQTT_DEVICES_TOPIC = "test/devices"
MQTT_SENSORS_TOPIC = "test/sensors"