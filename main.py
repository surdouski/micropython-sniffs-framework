import asyncio
from msf.startup import *  # used to start on device


# maybe just pull this in from mr. hinch in primitives repo
def set_global_exception():
    def _handle_exception(loop, context):
        import sys

        sys.print_exception(context["exception"])
        sys.exit()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(_handle_exception)

set_global_exception()


try:
    asyncio.run(startup())
except Exception as exception:
    print(exception)
    import time
    time.sleep(1)
    asyncio.new_event_loop()
