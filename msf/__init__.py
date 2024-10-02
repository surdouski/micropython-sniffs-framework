from pathlib import Path
from msf.settings import *  # Import default settings

user_settings_path = Path(__file__).parent.parent / "settings.py"

def load_user_settings():
    if user_settings_path.exists():
        # Dynamically import the user-defined settings
        user_settings_module = __import__("settings", globals(), locals(), [], 0)

        # Override default settings with user-defined settings
        for setting in dir(user_settings_module):
            if not setting.startswith("__"):
                globals()[setting] = getattr(user_settings_module, setting)


load_user_settings()

from .device._device import *

# TODO: Should be using these probably, update later when things are changing less
# from .device._device import DevicesRegistry, DeviceSettingsValidationError, Device, Settings, Setting
# __all__ = [ "DevicesRegistry", "DeviceSettingsValidationError", "Device", "Settings", "Setting"]