# Micropython Sniffs Framework

Note: This will eventually encompass and/or use all the tools and utilities that are currently distributed across many
repos. It is currently a WIP.


## Devices

Device schemas go in the `/devices` directory and end with `.json`, (for example, `/devices/water_pump.json`).

_/devices/water_pump.json_
```json
{
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
}
```

The JSON must adhere to the following rules:
- Setting names can't contain the `.` character.
- Every setting must define a value, type, and description.
- The value, type, and description must all be strings. The value will be converted to and from a string using the type definition.
- Currently supported types are `(float/int/str)`.

The name of the device is the name of the file without the `.json` (the device name for `water_pump.json` is `water_pump`).