import asyncio
import time

import evdev
import lirc
from lirc.exceptions import (
    LircdCommandFailureError,
    LircdConnectionError,
    LircdInvalidReplyPacketError,
    LircdSocketError,
    LircError,
    UnsupportedOperatingSystemError,
)
from logger import logger
from remote import Remote

# other constants
RETRY_TIME_SECONDS = 5

# keyboard input codes
MUTE_CODE = 113
VOLUME_DOWN_CODE = 114
VOLUME_UP_CODE = 115
F1_CODE = 59
F2_CODE = 60
F3_CODE = 61
F4_CODE = 62
F5_CODE = 63
F6_CODE = 64
ESCAPE_CODE = 1
TAB_CODE = 15
EQUALS_CODE = 13
NUM_LOCK_CODE = 69
SLASH_CODE = 98
STAR_CODE = 55
BACKSPACE_CODE = 14
NUM_7_CODE = 71
NUM_8_CODE = 72
NUM_9_CODE = 73
MINUS_CODE = 74
NUM_4_CODE = 75
NUM_5_CODE = 76
NUM_6_CODE = 77
PLUS_CODE = 78
NUM_1_CODE = 79
NUM_2_CODE = 80
NUM_3_CODE = 81
NUM_0_CODE = 82
PERIOD_CODE = 83
ENTER_CODE = 96

# 6 key macropad triggers
MACROPAD_VOLUME_UP_TRIGGER = F1_CODE
MACROPAD_VOLUME_DOWN_TRIGGER = F4_CODE
MACROPAD_TOGGLE_DJ_TV_MODE_TRIGGER = F3_CODE
MACROPAD_TOGGLE_KITCHEN_SPEAKERS_TRIGGER = F6_CODE
MACROPAD_TOGGLE_SURROUND_MODE_TRIGGER = F2_CODE
MACROPAD_TOGGLE_DISCO_LIGHT_RED_YELLOW_TRIGGER = F5_CODE

# numpad triggers
NUMPAD_VOLUME_DOWN_TRIGGER = NUM_1_CODE
NUMPAD_VOLUME_UP_TRIGGER = NUM_2_CODE
NUMPAD_TV_MODE_TRIGGER = NUM_4_CODE
NUMPAD_DJ_MODE_TRIGGER = NUM_5_CODE
NUMPAD_KITCHEN_SPEAKERS_ON_TRIGGER = NUM_7_CODE
NUMPAD_KITCHEN_SPEAKERS_OFF_TRIGGER = NUM_8_CODE
NUMPAD_DISCO_LIGHT_WHITE_TRIGGER = BACKSPACE_CODE
NUMPAD_DISCO_LIGHT_YELLOW_TRIGGER = MINUS_CODE
NUMPAD_DISCO_LIGHT_RED_TRIGGER = PLUS_CODE
NUMPAD_DISCO_LIGHT_TOGGLE_TRIGGER = ENTER_CODE
NUMPAD_SPOTIFY_DARK_MODE_TRIGGER = TAB_CODE
NUMPAD_TV_POWER_TRIGGER = EQUALS_CODE
NUMPAD_TOGGLE_SURROUND_MODE_TRIGGER = NUM_0_CODE

CompoundException = (
    LircError,
    LircdSocketError,
    LircdConnectionError,
    LircdInvalidReplyPacketError,
    LircdCommandFailureError,
    UnsupportedOperatingSystemError,
)


def custom_exception_handler(loop, context):
    # first, handle with default handler
    loop.default_exception_handler(context)

    exception = context.get("exception")
    logger.info("IN THE HANDLER, HERE'S THE EXCEPTION (type first, then exception):")
    logger.info(type(exception))
    logger.exception(exception)

    if isinstance(exception, OSError):
        print(context)
        logger.info(
            "the above printed error is an OSError,"
            + " which is probably the keyboard being disconnected"
        )
        loop.stop()

    logger.info("DONE WITH HANDLER")


async def handle_events(device: evdev.InputDevice, remote: Remote):
    print("in handle_events")
    async for event in device.async_read_loop():
        if event.type == evdev.ecodes.ecodes["EV_KEY"]:
            # logger.info("GOT EVENT:")
            # logger.info(evdev.categorize(event))
            # logger.info(event.value)
            # logger.info(event.code)

            # TODO: handle these async on new threads so we can keep handling keyboard input
            # this will fix the queueing problem and allow for a kill switch
            # TODO: came back here 8 months later to add the same comment
            # maybe 8 months from now I'll actually fix it

            # push key event
            if event.value == 1:
                if (
                    event.code == MACROPAD_VOLUME_DOWN_TRIGGER
                    or event.code == NUMPAD_VOLUME_DOWN_TRIGGER
                ):
                    remote.start_holding_volume_down()

                if (
                    event.code == MACROPAD_VOLUME_UP_TRIGGER
                    or event.code == NUMPAD_VOLUME_UP_TRIGGER
                ):
                    remote.start_holding_volume_up()
                if event.code == MACROPAD_TOGGLE_DJ_TV_MODE_TRIGGER:
                    remote.toggle_input_tv_to_dj()
                if event.code == MACROPAD_TOGGLE_KITCHEN_SPEAKERS_TRIGGER:
                    remote.toggle_kitchen_speakers()
                if event.code == NUMPAD_KITCHEN_SPEAKERS_ON_TRIGGER:
                    remote.turn_kitchen_speakers_on()
                if event.code == NUMPAD_KITCHEN_SPEAKERS_OFF_TRIGGER:
                    remote.turn_kitchen_speakers_off()
                if (
                    event.code == MACROPAD_TOGGLE_SURROUND_MODE_TRIGGER
                    or event.code == NUMPAD_TOGGLE_SURROUND_MODE_TRIGGER
                ):
                    remote.toggle_surround_mode()
                if event.code == MACROPAD_TOGGLE_DISCO_LIGHT_RED_YELLOW_TRIGGER:
                    remote.toggle_disco_light_red_yellow()
                if event.code == NUMPAD_DJ_MODE_TRIGGER:
                    remote.switch_to_dj_mode()
                if event.code == NUMPAD_TV_MODE_TRIGGER:
                    remote.switch_to_tv_mode()
                if event.code == NUMPAD_DISCO_LIGHT_WHITE_TRIGGER:
                    remote.turn_disco_light_white()
                if event.code == NUMPAD_DISCO_LIGHT_YELLOW_TRIGGER:
                    remote.turn_disco_light_yellow()
                if event.code == NUMPAD_DISCO_LIGHT_RED_TRIGGER:
                    remote.turn_disco_light_red()
                if event.code == NUMPAD_DISCO_LIGHT_TOGGLE_TRIGGER:
                    remote.toggle_disco_light_power()
                if event.code == NUMPAD_SPOTIFY_DARK_MODE_TRIGGER:
                    remote.toggle_spotify_dark_mode()
                if event.code == NUMPAD_TV_POWER_TRIGGER:
                    remote.toggle_tv_power()

            # release key event
            if event.value == 0:
                if (
                    event.code == MACROPAD_VOLUME_DOWN_TRIGGER
                    or event.code == NUMPAD_VOLUME_DOWN_TRIGGER
                ):
                    remote.stop_holding_volume_button()
                if (
                    event.code == MACROPAD_VOLUME_UP_TRIGGER
                    or event.code == NUMPAD_VOLUME_UP_TRIGGER
                ):
                    remote.stop_holding_volume_button()


async def listen_to_keyboard_events(remote):
    logger.info("starting asyncio event loop")

    async with asyncio.TaskGroup() as tg:
        for path_to_device in [
            "/dev/input/by-id/usb-1189_8890-event-if02",
            "/dev/input/by-id/usb-1189_8890-if02-event-kbd",
            "/dev/input/by-id/usb-1189_8890-event-kbd",
            "/dev/input/by-id/usb-1189_8890-if03-event-mouse",
            "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-event-kbd",  # good
            # "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-if01-event-mouse",  # good (probably unnecessary)
            # "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-event-if01",  # good (probably unnecessary)
            # "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-if01-mouse", # breaks
        ]:
            tg.create_task(handle_events(evdev.InputDevice(path_to_device), remote))

    # loop = asyncio.get_event_loop()
    # loop.set_exception_handler(custom_exception_handler)
    # loop.run_forever()
    logger.info(
        "if we get here, that means we gracefully caught an exception in"
        + "custom_exception_handler. we can let this function return"
    )


def main():
    logger.info("--------------------------------------------")
    logger.info("starting up volume control server")
    lirc_client = lirc.Client()
    remote = Remote(lirc_client)

    while True:
        try:
            asyncio.run(listen_to_keyboard_events(remote))
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
                    + "the keyboard was unplugged at startup:"
                )
                logger.exception(e)
                logger.info(
                    f"waiting {RETRY_TIME_SECONDS} seconds and then trying again"
                )
                time.sleep(RETRY_TIME_SECONDS)
            if isinstance(e, OSError):
                logger.info(
                    "caught OSError, that probably means the keyboard got unplugged:"
                )
                logger.exception(e)
                logger.info(
                    f"waiting {RETRY_TIME_SECONDS} seconds and then trying again"
                )
                time.sleep(RETRY_TIME_SECONDS)
            else:
                logger.info("caught some other type of error. quitting")
                logger.exception(e)
                break


if __name__ == "__main__":
    main()
