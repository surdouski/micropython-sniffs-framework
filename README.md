# Micropython Sniffs Framework

Note: This will eventually encompass and/or use all the tools and utilities that are currently distributed across many
repos. It is currently a WIP.

## What is the purpose of this project?

I want to create a micropython-native framework for IoT. I don't like the current state of IoT related to:

1. Cloud services and IoT: (TLDR; I hate services.) In the past, these services would have been libraries or utilities that
anyone could have used/downloaded/installed. Now, instead, they turn it into a black box application, difficult to interact
with, requiring registration and an account, and of course is behind a paywall. Yuck. No thanks.
2. Top-down configuration/control schemes: I don't have as many reservations about this as I do services. I think
it's fine to have a central server that defines everything and controls your devices. However, I think a framework
that explicitly defines its schemas and interactions between other parts of the system is an approach that has
less overhead, allows devices to exist and operate on their own, and gives more flexibility to mold and design your own
solution based on the constraints of your project -- all while giving you the solid foundation to build on with sensible
defaults and scaffolding.

I think this is a big project with many tasks and I don't purport to have all the answers... yet. What I do have,
however, is the motivation to continue working on this project (and hopefully help some people in the process, as
that's really what this is all about).

I'm going to start small, meticulously create large amounts of documentation that
very well might rival or exceed the amount of code, and try to stay focused on tasks that help common development workflow's. I
will achieve this dogfooding my own framework consistently to develop on my own projects. I might even start writing about
them as well in a blog post format so that others can follow along. I don't trust anyone that makes a framework just to
make a framework. A framework should solve common problems and offer a variety tools that are actually needed.  

## Installation

~~Will write a more in depth approach to installations, but I am putting a `package.json` in most directories,
each of them defining the requirements of that directory and any subdirectories. This should allow for easy
installation of specific components of the project as the codebase becomes larger.~~ To simplify development for now,
I am leaving a single `package.json` at the top level for installation, since the project is not large. So, for now,
simply install with the following command:

```bash
mpremote mip install github:surdouski/micropython-sniffs-framework 
```

## Device/Setting

### Why should I use these `Device` and `Setting` classes?

When defining your objects with these classes, you get some predefined behavior for free.
- Live setting changes are maintained through hardware reboots.
- Live setting changes managed and routed through framework-defined MQTT topic patterns. Just define a `MQTT_DEVICES_TOPIC`
in the `settings.py` (or use the default) and the framework will manage the process of updating settings for you. There
is currently a tool used for viewing and updating device settings on the command line: https://github.com/surdouski/device-ops. You
can install it through pipx (recommended) or pip: `pipx install device-ops` _Note: The
tool might eventually be renamed, but it is guaranteed to continue existing and be compatible for use within this framework._
- Decorators to trigger on setting updates. (`@setting_foo.on_update()` decorated on a function calls that function with
the new value whenever that setting is updated). 
- Guaranteed compatability with the rest of the framework's features, as development continues.


### Creating new devices with settings

To define a device and settings, simply create `Setting` objects and pass them to `Device`.

```python
from msf.device import Device, Setting

setting_1 = Setting(name="setting_1", value=4.0, description="The number 4, as a float.")
setting_2 = Setting(name="setting_2", value=3, description="The number 3, as an int.")
device = Device(device_name="water_pump", settings=[setting_1,setting_2])
```

This will either create a new saved state in the device settings, or for any settings that had previously been defined,
it will pull the value from the state instead.

For instance, if you had already saved a device with the above settings, but had updated the `setting_1` to `5.0`, your
`setting_1.value` would be `5.0` after the Device instantiation:

```python
# saved state for setting_1.value is currently "5.0"
setting_1 = Setting(name="setting_1", value=4.0, description="The number 4, as a float.")
print(setting_1.value)  # before Device instantiation: 4.0
device = Device(device_name="water_pump", settings=[setting_1])
print(setting_1.value)  # after Device instantiation: 5.0
```

Loading the state in this way ensures you don't lose your changed/updated settings during a hardware reboot.


### Decorators for Settings

I plan to have more than just one of these.

#### `on_update`

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

Whenever the `duty_u16` setting was updated, it would trigger the `pump_change_duty_cycle` function and update
the `PWM` to use the `new_value`. The setting could be updated non-locally through the `device-ops`
tool, with the following command:

```bash
dops devices water_pump duty_u16 --set=4000 --type=int
```

_Note: In the future, the need to specify the type, e.g. `--type=int` will go away, as that's validated on the hardware now._


### How to access current device settings

Simple ways to access your current devices and settings.

#### Access settings on the device instance instance

```python
from msf.device import Setting, Device
setting_1 = Setting(name="setting_1", value=42, description="The answer to the question.")
my_device = Device(device_name="my_device", settings=[setting_1])

foo_ref_to_setting_1 = my_device.settings.get("setting_1")
bar_ref_to_setting_1 = my_device.settings["setting_1"]  # if you aren't worried about a KeyError
```

#### Imports

You can simply import your `Device` or `Setting` objects into other modules.

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

Alternatively, you can use the singleton `DevicesRegistry` for access.

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
- No keys can contain `.` character.
- Every setting has a value, type, and description.
- The value, type, and description must all be strings. The value will be converted to and from a string using the type definition.
- Currently supported types are `(float/int/str)`.