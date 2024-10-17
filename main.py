# TODO: This is not a file that is meant for the project, it's a file to showcase something. Should be in a statics
#   folder or something, but lets deal with it at a later date.

import asyncio
from msf.startup import startup  # loads startup logic, probably want to move startup loading into __init__.py though for the project. unsure yet, leaving as is for now.
# from msf.device import Device, Setting

# duty_u16 = Setting(name="duty_u16", value=8192, description="For use in PWM of pump.")
# water_pump = Device(device_name="water_pump", settings=[duty_u16])
#
# @duty_u16.on_update()
# def pump_change_duty_cycle(new_value):
#     print(f"Adjusted PWM value: {new_value}")  # instead of adjusting the pwm, lets just print it for the demo


def set_global_exception():
    def handle_exception(_loop, context):
        import sys

        print("Irrecoverable exception bubbled up.")
        print(f"Exception details: {context['exception']}")
        print("Resetting board")
        sys.print_exception(context["exception"])
        sys.exit()

    print("Getting event loop")
    _loop = asyncio.get_event_loop()

    print("Setting exception handler")
    _loop.set_exception_handler(handle_exception)

set_global_exception()

from msf.sensor import LocalSensor, RemoteSensor

# sensor = LocalSensor(name="inside_temp")
remote_sensor = RemoteSensor(name="foo_reading")

@remote_sensor.on_update()
def print_reading(new_value):
    print(new_value)
    print(remote_sensor.value)  # Should be the same


async def main():
    await startup()
    # await sensor.update(99)
    while True:
        await asyncio.sleep(10)

try:
    asyncio.run(main())
except Exception as exception:
    print(exception)
    import time
    time.sleep(1)
    asyncio.new_event_loop()

