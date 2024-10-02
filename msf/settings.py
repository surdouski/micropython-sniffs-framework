# settings.py
# Similar to the new project directory, settings.py is used for identifying locations of
# different modules and files.
from pathlib import Path


DOT_SETTINGS_DIR_PATH = Path("/.settings")
DEVICES_SETTINGS_PATH = DOT_SETTINGS_DIR_PATH / "devices.json"

CONFIG_DIR_PATH = Path("/.config")
MQTT_AS_CONFIG_PATH = CONFIG_DIR_PATH / "mqtt_as.json"

MQTT_DEVICES_TOPIC = "test/devices"  # Do not start mqtt topic's with a "/"