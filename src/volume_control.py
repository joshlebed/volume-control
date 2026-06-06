import asyncio
import time

import evdev
import lirc
from coordinator import Coordinator
from logger import logger
from remote import Remote

# other constants
RETRY_TIME_SECONDS = 5


def custom_exception_handler(loop, context):
    # first, handle with default handler
    loop.default_exception_handler(context)

    exception = context.get("exception")
    logger.info("IN THE HANDLER, HERE'S THE EXCEPTION (type first, then exception):")
    logger.info(type(exception))
    logger.exception(exception)

    if isinstance(exception, OSError):
        logger.info(context)
        logger.info(
            "the above printed error is an OSError,"
            + " which is probably the keyboard being disconnected"
        )
        loop.stop()

    logger.info("DONE WITH HANDLER")


async def handle_events(device: evdev.InputDevice, coordinator: Coordinator):
    async for event in device.async_read_loop():
        if event.type == evdev.ecodes.ecodes["EV_KEY"]:
            coordinator.handle_keyboard_event(event)


async def listen_to_keyboard_events(coordinator):
    logger.info("starting asyncio event loop")

    async with asyncio.TaskGroup() as tg:
        for path_to_device in [
            # old 6 key
            # "/dev/input/by-id/usb-1189_8890-event-if02",
            # "/dev/input/by-id/usb-1189_8890-if02-event-kbd",
            # "/dev/input/by-id/usb-1189_8890-event-kbd",
            # "/dev/input/by-id/usb-1189_8890-if03-event-mouse",
            # wireless numpad
            "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-event-kbd",  # good
            # "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-if01-event-mouse",  # good (probably unnecessary)
            # "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-event-if01",  # good (probably unnecessary)
            # "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-if01-mouse", # breaks
            # new 2 key macropad
            "/dev/input/by-id/usb-5131_FQ-K002_RGB-event-kbd",
            # "/dev/input/by-id/usb-5131_FQ-K002_RGB-if01-event-mouse",
            # "/dev/input/by-id/usb-5131_FQ-K002_RGB-if01-mouse",
            # "/dev/input/by-id/usb-5131_FQ-K002_RGB-if02-event-joystick",
            # "/dev/input/by-id/usb-5131_FQ-K002_RGB-if02-joystick",
        ]:
            tg.create_task(
                handle_events(evdev.InputDevice(path_to_device), coordinator)
            )

    # loop = asyncio.get_event_loop()
    # loop.set_exception_handler(custom_exception_handler)
    # loop.run_forever()
    logger.info(
        "if we get here, that means we gracefully caught an exception in"
        + "custom_exception_handler. we can let this function return"
    )


def fresh_lirc_client(old_client: lirc.Client) -> lirc.Client:
    """Replace a possibly-desynced lircd connection with a fresh one.

    A send_stop() timeout mid-repeat leaves the old socket permanently
    desynced (every later command times out) and can leave lircd stuck
    repeating a key. Close the old connection, open a new one, and
    best-effort stop any orphaned repeat.
    """
    try:
        old_client.close()
    except Exception:
        logger.info("failed to close old lirc client, continuing anyway")

    client = lirc.Client()
    try:
        client.send_stop()
    except Exception:
        pass  # "not repeating" is the normal case

    return client


def main():
    logger.info("--------------------------------------------")
    logger.info("starting up volume control server")
    remote = Remote(lirc.Client())
    coordinator = Coordinator(remote)

    while True:
        try:
            asyncio.run(listen_to_keyboard_events(coordinator))
        except ExceptionGroup as e_group:
            logger.info("caught ExceptionGroup. parsing")

            if len(e_group.exceptions) < 1:
                logger.info("caught empty ExceptionGroup. quitting")
                logger.exception(e_group)
                break

            e = e_group.exceptions[0]  # pylint: disable=unsubscriptable-object

            if isinstance(e, FileNotFoundError):
                logger.info(
                    "caught FileNotFoundError, that probably means"
                    + " the keyboard was unplugged at startup:"
                )
            elif isinstance(e, TimeoutError):
                logger.info(
                    "caught TimeoutError, that probably means the lircd"
                    + " socket desynced (e.g. send_stop raced a repeat):"
                )
            elif isinstance(e, OSError):
                logger.info(
                    "caught OSError, that probably means the keyboard got unplugged:"
                )
            else:
                logger.info(e)
                logger.info("caught some other type of error. quitting")
                logger.exception(e)
                break

            logger.exception(e)
            logger.info(f"waiting {RETRY_TIME_SECONDS} seconds and then trying again")
            time.sleep(RETRY_TIME_SECONDS)
            # don't let the retry inherit a poisoned lircd connection
            remote.client = fresh_lirc_client(remote.client)


if __name__ == "__main__":
    main()
