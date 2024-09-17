"""
docstring
"""

import asyncio
import logging
import time
import traceback
from enum import Enum, StrEnum
from logging.handlers import RotatingFileHandler

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


class RemoteID(StrEnum):
    ONKYO = "onkyo"
    ROKU = "roku"
    DISCO_LIGHT = "ADJ-REMOTE"


class OnkyoButton(StrEnum):
    KEY_POWER = "KEY_POWER"
    BTN_1 = "BTN_1"
    BTN_2 = "BTN_2"
    BTN_3 = "BTN_3"
    BTN_4 = "BTN_4"
    BTN_5 = "BTN_5"
    BTN_6 = "BTN_6"
    BTN_7 = "BTN_7"
    BTN_8 = "BTN_8"
    BTN_9 = "BTN_9"
    KEY_VOLUMEDOWN = "KEY_VOLUMEDOWN"
    KEY_VOLUMEUP = "KEY_VOLUMEUP"
    STEREO = "STEREO"
    SURROUND = "SURROUND"
    BTN_LISTENINGMODE_LEFT = "BTN_LISTENINGMODE_LEFT"
    BTN_LISTENINGMODE_RIGHT = "BTN_LISTENINGMODE_RIGHT"
    BTN_CH_SEL = "BTN_CH_SEL"
    BTN_LEVEL_MINUS = "BTN_LEVEL_MINUS"
    BTN_LEVEL_PLUS = "BTN_LEVEL_PLUS"
    KEY_SETUP = "KEY_SETUP"
    KEY_TV_POWER = "KEY_TV_POWER"


class RokuButton(StrEnum):
    KEY_BACK = "KEY_BACK"
    KEY_HOME = "KEY_HOME"
    KEY_UP = "KEY_UP"
    KEY_LEFT = "KEY_LEFT"
    KEY_OK = "KEY_OK"
    KEY_RIGHT = "KEY_RIGHT"
    KEY_DOWN = "KEY_DOWN"
    KEY_AGAIN = "KEY_AGAIN"
    KEY_INFO = "KEY_INFO"
    KEY_REWIND = "KEY_REWIND"
    KEY_PLAYPAUSE = "KEY_PLAYPAUSE"
    KEY_FASTFORWARD = "KEY_FASTFORWARD"


class HoldTime(Enum):
    KITCHEN_SPEAKERS = 3.5
    VOLUME_ALL_THE_WAY = 10
    VOLUME_0_TO_60 = 7.5
    VOLUME_0_TO_30 = 3.9


class DiscoLightColor(Enum):
    WHITE = "WHITE"
    RED = "RED"
    YELLOW = "YELLOW"


class ReceiverInputSource(Enum):
    TV = "TV"
    DJ = "DJ"


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
NUMPAD_DJ_MODE_TRIGGER = NUM_4_CODE
NUMPAD_TV_MODE_TRIGGER = NUM_5_CODE
NUMPAD_DISCO_LIGHT_WHITE_TRIGGER = BACKSPACE_CODE
NUMPAD_DISCO_LIGHT_YELLOW_TRIGGER = MINUS_CODE
NUMPAD_DISCO_LIGHT_RED_TRIGGER = PLUS_CODE
NUMPAD_DISCO_LIGHT_TOGGLE_TRIGGER = ENTER_CODE
NUMPAD_SPOTIFY_DARK_MODE_TRIGGER = TAB_CODE

CompoundException = (
    LircError,
    LircdSocketError,
    LircdConnectionError,
    LircdInvalidReplyPacketError,
    LircdCommandFailureError,
    UnsupportedOperatingSystemError,
)


LOG_FILE = "/tmp/volume_controller.log"
MY_HANDLER = RotatingFileHandler(
    LOG_FILE, mode="a", maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None, delay=0
)
MY_HANDLER.setLevel(logging.DEBUG)
logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)
logger.addHandler(MY_HANDLER)


# singleton pattern
class Remote:
    def __init__(self, client: lirc.Client):
        self.client = client
        self.busy = False
        self.dj_mode = False
        self.kitchen_speakers_on = True
        self.direct_mode = True
        self.disco_light_color = DiscoLightColor.RED
        self.is_disco_light_on = False
        self.receiver_input_source = ReceiverInputSource.TV

    # TODO: add wrap_with_busy

    # UTILS
    def send_to_remote(self, remote_id, msg):
        if self.busy:
            return
        self.busy = True

        try:
            self.client.send_once(remote_id, msg)
        except CompoundException:
            logger.error(traceback.format_exc())

        self.busy = False

    def send_to_remote_then_sleep(self, remote_id, msg, times):
        for _ in range(times):
            self.send_to_remote(remote_id, msg)
            time.sleep(0.2)

    def send_to_onkyo_then_sleep(self, msg, times=1):
        self.send_to_remote_then_sleep(RemoteID.ONKYO, msg, times)

    def send_to_roku_then_sleep(self, msg, times=1):
        self.send_to_remote_then_sleep(RemoteID.ROKU, msg, times)

    def send_to_disco_light_then_sleep(self, msg, times=1):
        self.send_to_remote_then_sleep(RemoteID.DISCO_LIGHT, msg, times)

    def press_and_hold_to_onkyo(self, msg, seconds=0):
        if self.busy:
            return
        self.busy = True

        self.client.send_start(RemoteID.ONKYO, msg)
        time.sleep(seconds)
        self.client.send_stop(RemoteID.ONKYO, msg)
        time.sleep(0.2)

        self.busy = False

    # VOLUME CONTROLS
    def start_holding_volume_down(self):
        logger.info("volume down")
        if self.busy:
            return
        self.busy = True

        self.client.send_start(RemoteID.ONKYO, OnkyoButton.KEY_VOLUMEDOWN)

    def start_holding_volume_up(self):
        logger.info("volume up")
        if self.busy:
            return
        self.busy = True

        self.client.send_start(RemoteID.ONKYO, OnkyoButton.KEY_VOLUMEUP)

    def stop_holding_volume_button(self):
        logger.info("done with volume buttons")
        if not self.busy:
            return

        self.client.send_stop()
        self.busy = False

    # RECEIVER INPUT
    def switch_to_dj_mode(self):
        logger.info("switching to dj mode")

        self.receiver_input_source = ReceiverInputSource.DJ

        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEDOWN, HoldTime.VOLUME_ALL_THE_WAY.value
        )
        self.send_to_onkyo_then_sleep(OnkyoButton.KEY_TV_POWER)
        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEUP, HoldTime.VOLUME_0_TO_60.value
        )

        logger.info("done switching to dj mode")

    def switch_to_tv_mode(self):
        logger.info("switching to tv mode")

        self.receiver_input_source = ReceiverInputSource.TV

        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEDOWN, HoldTime.VOLUME_ALL_THE_WAY.value
        )
        self.send_to_onkyo_then_sleep(OnkyoButton.KEY_TV_POWER)
        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEUP, HoldTime.VOLUME_0_TO_30.value
        )

        logger.info("done switching to tv mode")

    def toggle_input_tv_to_dj(self):
        logger.info("toggling input between tv/dj")
        self.clear_menu_state()

        if self.receiver_input_source == ReceiverInputSource.TV:
            self.switch_to_dj_mode()

        else:
            self.switch_to_tv_mode()

    # KITCHEN SPEAKERS
    def turn_kitchen_speakers_off(self):
        logger.info("turning kitchen speakers off")
        try:
            self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 5)
            self.press_and_hold_to_onkyo(
                OnkyoButton.BTN_LEVEL_MINUS, HoldTime.KITCHEN_SPEAKERS.value
            )
            self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 1)
            self.press_and_hold_to_onkyo(
                OnkyoButton.BTN_LEVEL_MINUS, HoldTime.KITCHEN_SPEAKERS.value
            )
        except CompoundException:
            logger.error(traceback.format_exc())
        logger.info("done turning kitchen speakers off")

    def turn_kitchen_speakers_on(self):
        logger.info("turning kitchen speakers on")
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 5)
        self.press_and_hold_to_onkyo(
            OnkyoButton.BTN_LEVEL_PLUS, HoldTime.KITCHEN_SPEAKERS.value
        )
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LEVEL_MINUS, 4)
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 1)
        self.press_and_hold_to_onkyo(
            OnkyoButton.BTN_LEVEL_PLUS, HoldTime.KITCHEN_SPEAKERS.value
        )
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LEVEL_MINUS, 4)
        logger.info("done turning kitchen speakers on")

    def clear_menu_state(self):
        logger.info("clearing menu state")
        self.send_to_onkyo_then_sleep(OnkyoButton.KEY_SETUP, 2)

    def toggle_kitchen_speakers(self):
        logger.info("toggling kitchen speakers on/off")

        self.clear_menu_state()

        if not self.kitchen_speakers_on:
            self.turn_kitchen_speakers_on()
            self.kitchen_speakers_on = True

        else:
            self.turn_kitchen_speakers_off()
            self.kitchen_speakers_on = False

    # SURROUND SOUND MODE
    def switch_to_all_channel_stereo(self):
        logger.info("switching to all channel stereo")
        self.send_to_onkyo_then_sleep(OnkyoButton.STEREO)
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LISTENINGMODE_LEFT, 4)
        logger.info("done switching to all channel stereo")

    def switch_to_direct(self):
        logger.info("switching to direct")
        self.send_to_onkyo_then_sleep(OnkyoButton.STEREO)
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LISTENINGMODE_LEFT)
        logger.info("done switching to direct")

    def toggle_surround_mode(self):
        logger.info("toggling surround mode between all channel stereo and direct")

        self.clear_menu_state()

        if not self.direct_mode:
            self.switch_to_direct()
            self.direct_mode = True

        else:
            self.switch_to_all_channel_stereo()
            self.direct_mode = False

    # DISCO LIGHT CONTROLS
    def turn_disco_light_white(self):
        self.disco_light_color = DiscoLightColor.WHITE
        logger.info("turning disco light to single color white mode")
        self.send_to_disco_light_then_sleep("COLOR")
        self.send_to_disco_light_then_sleep("9")
        logger.info("done turning disco light to single color yellow mode")

    def turn_disco_light_yellow(self):
        self.disco_light_color = DiscoLightColor.YELLOW
        logger.info("turning disco light to single color yellow mode")
        self.send_to_disco_light_then_sleep("COLOR")
        self.send_to_disco_light_then_sleep("2")
        logger.info("done turning disco light to single color yellow mode")

    def turn_disco_light_red(self):
        self.disco_light_color = DiscoLightColor.RED
        logger.info("turning disco light to single color red mode")
        self.send_to_disco_light_then_sleep("COLOR")
        self.send_to_disco_light_then_sleep("1")
        logger.info("done turning disco light to single color red mode")

    def turn_disco_light_on(self):
        self.is_disco_light_on = True
        logger.info("turning disco light on")
        self.send_to_disco_light_then_sleep("STAND_BY")
        self.send_to_disco_light_then_sleep("2")
        logger.info("done turning disco light to single color yellow mode")

    def turn_disco_light_off(self):
        self.is_disco_light_on = False

    def toggle_disco_light_red_yellow(self):
        logger.info("toggling disco spotlight between red and yellow")

        if self.disco_light_color == DiscoLightColor.YELLOW:
            self.turn_disco_light_red()

        else:
            self.turn_disco_light_yellow()

    def toggle_disco_light_power(self):
        logger.info("toggling disco spotlight power on/off")
        self.send_to_disco_light_then_sleep("STAND_BY")

    def turn_on_spotify_dark_mode(self):
        logger.info("turning on spotify dark mode")
        self.send_to_roku_then_sleep(RokuButton.KEY_UP)


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
                if event.code == MACROPAD_TOGGLE_SURROUND_MODE_TRIGGER:
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
                    remote.turn_on_spotify_dark_mode()

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
            "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-if01-event-mouse",  # good (probably unnecessary)
            "/dev/input/by-id/usb-MOSART_Semi._2.4G_Keyboard_Mouse-event-if01",  # good (probably unnecessary)
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
