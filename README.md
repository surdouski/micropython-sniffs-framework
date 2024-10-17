# Micropython Sniffs Framework

## What is the purpose of this project?

To create a micropython-native framework for IoT, with no services or accounts to sign up for to use. It's a library/framework; not a business model.

To provide a more decentralized IoT framework option. Allow devices to exist/operate on their own without needing to define a configuration for them off-device. This allows for additional framework components that can be added/removed based on a project's needs (more components will be introduced in the future, including external storage, monitoring, analysis, and more).

## Installation

Recommended cli tool specific to this project: [msf-cli](https://github.com/surdouski/msf-cli). It can help with setting up an initial project and running a local MQTT broker for testing the application:

```bash
pipx install msf-cli
```

The `msf` framework package itself can be downloaded with (skip this if using the `msf-cli` tool):

```bash
mpremote mip install github:surdouski/micropython-sniffs-framework 
```

## Sensor

Provides a communication mechanism for sensor values over the network and between hardware components.

### What are `LocalSensor` and `RemoteSensor` classes for?

- Communication of `LocalSensor` values passed to any other hardware currently running msf that defines a `RemoteSensor` with the same name.
- Decorators to trigger on sensor updates. (`@remote_sensor_foo.on_update()` decorated on a function calls that function with the new value whenever that sensor value is updated).

### Usage

`RemoteSensor` on one hardware device:

```python
from msf.sensor import RemoteSensor
remote_sensor_foo = RemoteSensor(name="foo_sensor")

@remote_sensor_foo.on_update()
def on_update_foo(value):
    print(value)
```

`LocalSensor` on another hardware device:

```python
from msf.sensor import LocalSensor
local_sensor_foo = LocalSensor(name="foo_sensor")
local_sensor_foo.update(42)
```

When `local_sensor_foo.update(42)` is called, the other hardware device with `remote_sensor_foo` defined will print `42`.

Note: The default MQTT topic for sensors is `test/sensors`. This can be changed by updating `MQTT_SENSORS_TOPIC` in `settings.py`.

### Retrieval of sensors

To access a `LocalSensor` through the registry:

```python
from msf.sensor import LocalSensorsRegistry
local_sensors_registry = LocalSensorsRegistry()
foo_sensor = local_sensors_registry.get("local_sensor_foo")  # only works if the firmware on device already defined this
```

To access a `RemoteSensor` through the registry:

```python
from msf.sensor import RemoteSensorsRegistry
remote_sensors_registry = RemoteSensorsRegistry()
foo_sensor = remote_sensors_registry.get("remote_sensor_foo")  # only works if the firmware on device already defined this
```

Note: Registries will not retrieve across hardware devices boundaries. They are for static retrieval of locally defined objects.

## Device/Setting

Provides stateful configuration management for firmware. Can be managemed remotely and persists through hardware resets.

### What are `Device` and `Setting` classes for?

- Live setting changes are maintained through hardware reboots.
- Decorators to trigger on setting updates. (`@setting_foo.on_update()` decorated on a function calls that function with the new value whenever that setting is updated).


### Usage

To define a device and settings, create `Setting` objects and pass them to `Device`.

```python
from msf.device import Device, Setting

setting_1 = Setting(name="setting_1", value=4.0, description="The number 4, as a float.")
setting_2 = Setting(name="setting_2", value=3, description="The number 3, as an int.")
device = Device(device_name="water_pump", settings=[setting_1,setting_2])
```

This will either create a new saved state in the device settings, or for any settings that had previously been defined, it will pull the value from the state instead.

For instance, if a device was saved with the above settings, but had updated the `setting_1` to `5.0`, the `setting_1.value` would be `5.0` after the Device instantiation:

```python
# saved state for setting_1.value is currently "5.0"
setting_1 = Setting(name="setting_1", value=4.0, description="The number 4, as a float.")
print(setting_1.value)  # before Device instantiation: 4.0
device = Device(device_name="water_pump", settings=[setting_1])
print(setting_1.value)  # after Device instantiation: 5.0
```

Loading the state in this way ensures changed/updated settings are not lost because of a hardware reboot.

Note: The default MQTT topic for sensors is `test/devices`. This can be changed by updating `MQTT_DEVICES_TOPIC` in `settings.py`.

### Decorators for Settings

#### Using `on_update()`

When a setting is updated (except for the `Device` instantiation), this decorated function is called with the new setting value.

An example of how this might be used in practice:

```python
from msf.device import Device, Setting
from machine import PWM

duty_u16 = Setting(name="duty_u16", value=8192, description="For use in PWM of pump.")
water_pump = Device(device_name="water_pump", settings=[duty_u16])
pwm = PWM(pin, freq=50, duty_u16=duty_u16.value)

@duty_u16.on_update()
def pump_change_duty_cycle(new_value):
    pwm.duty_u16(new_value)
```

Whenever the `duty_u16` setting was updated, it would trigger the `pump_change_duty_cycle` function and update the `PWM` to use the `new_value`. The setting could be updated non-locally through the `msf-cli` tool, with the following command:

```bash
msf devices water_pump duty_u16 --set 4000
```

More information on using the `msf-cli` tool can be found [here](https://github.com/surdouski/msf-cli). 

### How to access current device settings


```python
from msf.device import Setting, Device
setting_1 = Setting(name="setting_1", value=42, description="The answer to the question.")
my_device = Device(device_name="my_device", settings=[setting_1])

foo_ref_to_setting_1 = my_device.settings.get("setting_1")
bar_ref_to_setting_1 = my_device.settings["setting_1"]  # alternatively, but can raise KeyError
```

#### Imports

Import `Device` or `Setting` objects into other modules:

_foo.py_
```python
from msf.device import Setting, Device
setting_1 = Setting(name="setting_1", value=42, description="The answer to the question.")
my_device = Device(device_name="my_device", settings=[setting_1])
```

_bar.py_
```python
from .foo import setting_1  # relative imports are actually evil, but this is just an example so it's fine
print(setting_1.value)  # 42, or whichever value was loaded from the saved state
```

#### DevicesRegistry

Alternatively, use the singleton `DevicesRegistry` for access:

_foo.py_
```python
from msf.device import Setting, Device
setting_1 = Setting(name="setting_1", value=42, description="The answer to the question.")
my_device = Device(device_name="my_device", settings=[setting_1])
```

_bar.py_
```python
from msf.device import DevicesRegistry
my_device = DevicesRegistry().devices.get("my_device")
setting_1 = my_device.settings.get("setting_1")
```

### Saved State

Devices settings save to the `DEVICES_SETTINGS_PATH` defined in `settings.py`. The default value is "/.settings/devices.json".

Example:

`/.settings/devices.json`
```json
{
  "water_pump": {
    "setting_1": {
      "value": "4.0",
      "type": "float",
      "description": "The description of setting 1."
    },
    "setting_2": {
      "value": "3",
      "type": "int",
      "description": "The description of setting 2."
    }
  },
  "another_device": {
    "other_device_setting_1": {
      "value": "some string",
      "type": "str",
      "description": "The description of other device setting 1."
    }
  }
}
```

The JSON adheres to the following rules:
- **Important: No keys can contain `.` character.**
- Every setting has a value, type, and description.
- The value, type, and description must all be strings. The value will be converted to and from a string using the type definition.
- Currently supported types are `(float/int/str)`.
