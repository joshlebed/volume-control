import asyncio
import time

import evdev
import lirc
from coordinator import Coordinator
from device_supervisor import supervise_device
from logger import logger
from remote import Remote

# other constants
RETRY_TIME_SECONDS = 5

# Physical keypads to read. Each path is supervised independently, so one keypad
# being unplugged (or simply absent at startup) never affects the others -- they
# each open -> read -> recover on their own. See device_supervisor.py for why.
DEVICE_PATHS = [
    # wireless numpad
    "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-event-kbd",
    # 2-key macropad
    "/dev/input/by-id/usb-5131_FQ-K002_RGB-event-kbd",
]

# Resolved once; evdev maps "EV_KEY" -> 1.
EV_KEY = evdev.ecodes.ecodes["EV_KEY"]


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


async def listen_to_keyboard_events(coordinator: Coordinator, remote: Remote):
    """Run one independent supervisor per keypad, forever.

    A disconnect on any single device is handled inside its own supervisor
    (reopen when it returns); a lircd desync is handled inline (recreate the
    client, keep reading). Neither reaches this TaskGroup, so the supervisors
    do not cancel each other. The TaskGroup only unwinds on a genuinely
    unexpected error, which main()'s loop then restarts.
    """
    logger.info("starting per-device supervisors for %d device(s)", len(DEVICE_PATHS))

    def on_lirc_desync():
        remote.client = fresh_lirc_client(remote.client)

    async with asyncio.TaskGroup() as tg:
        for path in DEVICE_PATHS:
            tg.create_task(
                supervise_device(
                    path,
                    lambda p=path: evdev.InputDevice(p),
                    coordinator.handle_keyboard_event,
                    is_key_event=lambda event: event.type == EV_KEY,
                    on_lirc_desync=on_lirc_desync,
                    retry_seconds=RETRY_TIME_SECONDS,
                )
            )


def main():
    logger.info("--------------------------------------------")
    logger.info("starting up volume control server")
    remote = Remote(lirc.Client())
    coordinator = Coordinator(remote)

    while True:
        try:
            asyncio.run(listen_to_keyboard_events(coordinator, remote))
            # Supervisors run forever; a normal return means the TaskGroup
            # exited without an exception (not expected). Restart it.
            logger.info("supervisors returned unexpectedly; restarting")
        except ExceptionGroup as e_group:
            # Last-resort catch-all. Expected device/lircd churn is handled
            # inside each supervisor and never reaches here, so anything that
            # does is unexpected -- log it, refresh a possibly-poisoned lircd
            # connection, back off, and restart all supervisors.
            logger.info("caught ExceptionGroup from supervisors; will restart")
            for exc in e_group.exceptions:
                logger.exception(exc)
            remote.client = fresh_lirc_client(remote.client)
        except Exception as exc:  # pylint: disable=broad-except
            logger.info("caught top-level %s; will restart", type(exc).__name__)
            logger.exception(exc)
            remote.client = fresh_lirc_client(remote.client)

        logger.info(f"waiting {RETRY_TIME_SECONDS} seconds and then trying again")
        time.sleep(RETRY_TIME_SECONDS)


if __name__ == "__main__":
    main()
