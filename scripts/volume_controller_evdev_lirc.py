"""
docstring
"""


import asyncio
import logging
import time
import traceback

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


# TODO: refactor these into enums
BTN_CH_SEL = "BTN_CH_SEL"
BTN_LEVEL_MINUS = "BTN_LEVEL_MINUS"
BTN_LEVEL_PLUS = "BTN_LEVEL_PLUS"
KEY_SETUP = "KEY_SETUP"
KITCHEN_SPEAKERS_HOLD_TIME = 3.5
VOLUME_ALL_THE_WAY_HOLD_TIME = 10
VOLUME_0_TO_60_HOLD_TIME = 7.5
VOLUME_0_TO_30_HOLD_TIME = 3.9
ONKYO_REMOTE_ID = "onkyo"
DISCO_LIGHT_REMOTE_ID = "ADJ-REMOTE"
ONKYO_VOLUME_DOWN_MESSAGE = "KEY_VOLUMEDOWN"
ONKYO_VOLUME_UP_MESSAGE = "KEY_VOLUMEUP"
ONKYO_TV_INPUT_MESSAGE = "BTN_1"
ONKYO_DJ_INPUT_MESSAGE = "BTN_2"
ONKYO_STEREO_MESSAGE = "STEREO"
ONKYO_LISTENING_MODE_LEFT = "BTN_LISTENINGMODE_LEFT"
ONKYO_LISTENING_MODE_RIGHT = "BTN_LISTENINGMODE_RIGHT"

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

# my custom triggers
VOLUME_UP_TRIGGER = F1_CODE
VOLUME_DOWN_TRIGGER = F4_CODE
TOGGLE_DJ_TV_MODE_TRIGGER = F3_CODE
TOGGLE_KITCHEN_SPEAKERS_TRIGGER = F6_CODE
TOGGLE_SURROUND_MODE_TRIGGER = F2_CODE
TOGGLE_DISCO_BALL_RED_YELLOW_TRIGGER = F5_CODE

CompoundException = (
    LircError,
    LircdSocketError,
    LircdConnectionError,
    LircdInvalidReplyPacketError,
    LircdCommandFailureError,
    UnsupportedOperatingSystemError,
)


# singleton pattern
class Remote:
    def __init__(self, client: lirc.Client):
        self.client = client
        self.busy = False
        self.dj_mode = False
        self.kitchen_speakers_on = True
        self.direct_mode = True
        self.disco_ball_red = True

    # UTILS
    def send_to_remote(self, remote_id, msg):
        self.client.send_once(remote_id, msg)

    def send_to_remote_then_sleep(self, remote_id, msg, times):
        for _ in range(times):
            self.send_to_remote(remote_id, msg)
            time.sleep(0.2)

    def send_to_onkyo_then_sleep(self, msg, times=1):
        self.send_to_remote_then_sleep(ONKYO_REMOTE_ID, msg, times)

    def send_to_disco_light_then_sleep(self, msg, times=1):
        self.send_to_remote_then_sleep(DISCO_LIGHT_REMOTE_ID, msg, times)

    def press_and_hold_to_onkyo(self, msg, seconds=0):
        self.client.send_start(ONKYO_REMOTE_ID, msg)
        time.sleep(seconds)
        self.client.send_stop(ONKYO_REMOTE_ID, msg)
        time.sleep(0.2)

    def wrap_lirc_exceptions(self, command):
        try:
            command()
        except CompoundException:
            logging.error(traceback.format_exc())

    # VOLUME CONTROLS
    def start_holding_volume_down(self):
        logging.info("volume down")
        if self.busy:
            return
        self.busy = True
        self.wrap_lirc_exceptions(
            lambda: self.client.send_start(ONKYO_REMOTE_ID, ONKYO_VOLUME_DOWN_MESSAGE)
        )

    def start_holding_volume_up(self):
        logging.info("volume up")
        if self.busy:
            return
        self.busy = True
        self.wrap_lirc_exceptions(
            lambda: self.client.send_start(ONKYO_REMOTE_ID, ONKYO_VOLUME_UP_MESSAGE)
        )

    def stop_holding_volume_button(self):
        logging.info("done with volume buttons")
        if not self.busy:
            return
        self.wrap_lirc_exceptions(lambda: self.client.send_stop())
        self.busy = False

    # RECEIVER INPUT
    def switch_to_dj_mode(self):
        logging.info("switching to dj mode")
        self.press_and_hold_to_onkyo(
            ONKYO_VOLUME_DOWN_MESSAGE, VOLUME_ALL_THE_WAY_HOLD_TIME
        )
        self.send_to_onkyo_then_sleep(ONKYO_DJ_INPUT_MESSAGE)
        self.press_and_hold_to_onkyo(ONKYO_VOLUME_UP_MESSAGE, VOLUME_0_TO_60_HOLD_TIME)
        logging.info("done switching to dj mode")

    def switch_to_tv_mode(self):
        logging.info("switching to tv mode")
        self.press_and_hold_to_onkyo(
            ONKYO_VOLUME_DOWN_MESSAGE, VOLUME_ALL_THE_WAY_HOLD_TIME
        )
        self.send_to_onkyo_then_sleep(ONKYO_TV_INPUT_MESSAGE)
        self.press_and_hold_to_onkyo(ONKYO_VOLUME_UP_MESSAGE, VOLUME_0_TO_30_HOLD_TIME)
        logging.info("done switching to tv mode")

    def toggle_input_tv_to_dj(self):
        logging.info("toggling input between tv/dj")
        if self.busy:
            return
        self.busy = True
        self.clear_menu_state()

        if self.dj_mode == False:
            self.wrap_lirc_exceptions(lambda: self.switch_to_dj_mode())
            self.dj_mode = True

        else:
            self.wrap_lirc_exceptions(lambda: self.switch_to_tv_mode())
            self.dj_mode = False

        self.busy = False

    # KITCHEN SPEAKERS
    def turn_kitchen_speakers_off(self):
        logging.info("turning kitchen speakers off")
        try:
            self.send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
            self.press_and_hold_to_onkyo(BTN_LEVEL_MINUS, KITCHEN_SPEAKERS_HOLD_TIME)
            self.send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
            self.press_and_hold_to_onkyo(BTN_LEVEL_MINUS, KITCHEN_SPEAKERS_HOLD_TIME)
        except CompoundException:
            logging.error(traceback.format_exc())
        logging.info("done turning kitchen speakers off")

    def turn_kitchen_speakers_on(self):
        logging.info("turning kitchen speakers on")
        self.send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
        self.press_and_hold_to_onkyo(BTN_LEVEL_PLUS, KITCHEN_SPEAKERS_HOLD_TIME)
        self.send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
        self.send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
        self.press_and_hold_to_onkyo(BTN_LEVEL_PLUS, KITCHEN_SPEAKERS_HOLD_TIME)
        self.send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
        logging.info("done turning kitchen speakers on")

    def clear_menu_state(self):
        logging.info("clearing menu state")
        self.send_to_onkyo_then_sleep(KEY_SETUP, 2)

    def toggle_kitchen_speakers(self):
        logging.info("toggling kitchen speakers on/off")
        if self.busy:
            return

        self.busy = True
        self.clear_menu_state()

        if self.kitchen_speakers_on == False:
            self.wrap_lirc_exceptions(lambda: self.turn_kitchen_speakers_on())
            self.kitchen_speakers_on = True

        else:
            self.wrap_lirc_exceptions(lambda: self.turn_kitchen_speakers_off())
            self.kitchen_speakers_on = False

        self.busy = False

    # SURROUND SOUND MODE
    def switch_to_all_channel_stereo(self):
        logging.info("switching to all channel stereo")
        self.send_to_onkyo_then_sleep(ONKYO_STEREO_MESSAGE)
        self.send_to_onkyo_then_sleep(ONKYO_LISTENING_MODE_LEFT, 4)
        logging.info("done switching to all channel stereo")

    def switch_to_direct(self):
        logging.info("switching to direct")
        self.send_to_onkyo_then_sleep(ONKYO_STEREO_MESSAGE)
        self.send_to_onkyo_then_sleep(ONKYO_LISTENING_MODE_LEFT)
        logging.info("done switching to direct")

    def toggle_surround_mode(self):
        logging.info("toggling surround mode between all channel stereo and direct")
        if self.busy:
            return
        self.busy = True
        self.clear_menu_state()

        if self.direct_mode == False:
            self.wrap_lirc_exceptions(lambda: self.switch_to_direct())
            self.direct_mode = True

        else:
            self.wrap_lirc_exceptions(lambda: self.switch_to_all_channel_stereo())
            self.direct_mode = False

        self.busy = False

    # DISCO BALL RED/YELLOW MODE
    def turn_disco_ball_yellow(self):
        logging.info("turning disco ball to single color yellow mode")
        self.send_to_disco_light_then_sleep("COLOR")
        self.send_to_disco_light_then_sleep("2")
        logging.info("done turning disco ball to single color yellow mode")

    def turn_disco_ball_red(self):
        logging.info("turning disco ball to single color red mode")
        self.send_to_disco_light_then_sleep("COLOR")
        self.send_to_disco_light_then_sleep("1")
        logging.info("done turning disco ball to single color red mode")

    def toggle_disco_ball_red_yellow(self):
        logging.info("toggling disco spotlight between red and yellow")
        if self.busy:
            return
        self.busy = True

        if self.disco_ball_red == False:
            self.wrap_lirc_exceptions(lambda: self.turn_disco_ball_red())
            self.disco_ball_red = True

        else:
            self.wrap_lirc_exceptions(lambda: self.turn_disco_ball_yellow())
            self.disco_ball_red = False

        self.busy = False


def custom_exception_handler(loop, context):
    # first, handle with default handler
    loop.default_exception_handler(context)

    exception = context.get("exception")
    logging.info("IN THE HANDLER, HERE'S THE EXCEPTION (type first, then exception):")
    logging.info(type(exception))
    logging.exception(exception)

    if isinstance(exception, OSError):
        print(context)
        logging.info(
            "the above printed error is an OSError, which is probably the keyboard being disconnected"
        )
        loop.stop()

    logging.info("DONE WITH HANDLER")


async def handle_events(device: evdev.InputDevice, remote: Remote):
    async for event in device.async_read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            # logging.info("GOT EVENT:")
            # logging.info(evdev.categorize(event))
            # logging.info(event.value)
            # logging.info(event.code)

            # push key event
            if event.value == 1:
                if event.code == VOLUME_DOWN_TRIGGER:
                    remote.start_holding_volume_down()
                if event.code == VOLUME_UP_TRIGGER:
                    remote.start_holding_volume_up()
                if event.code == TOGGLE_DJ_TV_MODE_TRIGGER:
                    remote.toggle_input_tv_to_dj()
                if event.code == TOGGLE_KITCHEN_SPEAKERS_TRIGGER:
                    remote.toggle_kitchen_speakers()
                if event.code == TOGGLE_SURROUND_MODE_TRIGGER:
                    remote.toggle_surround_mode()
                if event.code == TOGGLE_DISCO_BALL_RED_YELLOW_TRIGGER:
                    remote.toggle_disco_ball_red_yellow()

            # release key event
            if event.value == 0:
                if event.code == VOLUME_DOWN_TRIGGER:
                    remote.stop_holding_volume_button()
                if event.code == VOLUME_UP_TRIGGER:
                    remote.stop_holding_volume_button()


async def listen_to_keyboard_events(remote):
    logging.info("starting asyncio event loop")

    async with asyncio.TaskGroup() as tg:
        for path_to_device in [
            "/dev/input/by-id/usb-1189_8890-event-if02",
            "/dev/input/by-id/usb-1189_8890-if02-event-kbd",
            "/dev/input/by-id/usb-1189_8890-event-kbd",
            "/dev/input/by-id/usb-1189_8890-if03-event-mouse",
        ]:
            tg.create_task(handle_events(evdev.InputDevice(path_to_device), remote))

    # loop = asyncio.get_event_loop()
    # loop.set_exception_handler(custom_exception_handler)
    # loop.run_forever()
    logging.info(
        "if we get here, that means we gracefully caught an exception in"
        + "custom_exception_handler. we can let this function return"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("starting up volume control server")
    client = lirc.Client()
    remote = Remote(client)

    while True:
        try:
            asyncio.run(listen_to_keyboard_events(remote))
        except ExceptionGroup as e_group:
            logging.info("caught ExceptionGroup. parsing")

            if len(e_group.exceptions) < 1:
                logging.info("caught empty ExceptionGroup. quitting")
                logging.exception(e_group)
                break

            e = e_group.exceptions[0]

            if isinstance(e, FileNotFoundError):
                logging.info(
                    "caught FileNotFoundError, that probably means"
                    + "the keyboard was unplugged at startup:"
                )
                logging.exception(e)
                logging.info(
                    f"waiting {RETRY_TIME_SECONDS} seconds and then trying again"
                )
                time.sleep(RETRY_TIME_SECONDS)
            if isinstance(e, OSError):
                logging.info(
                    "caught OSError, that probably means the keyboard got unplugged:"
                )
                logging.exception(e)
                logging.info(
                    f"waiting {RETRY_TIME_SECONDS} seconds and then trying again"
                )
                time.sleep(RETRY_TIME_SECONDS)
            else:
                logging.info("caught some other type of error. quitting")
                logging.exception
                break


# unused


def input_loop():
    while True:
        a = input("next command (u or d): ")
        if a == "d":
            logging.info("vol down")
            try:
                client.send_once("onkyo", "KEY_VOLUMEDOWN")
            except CompoundException:
                logging.error(traceback.format_exc())

        elif a == "u":
            logging.info("vol up")
            try:
                client.send_once("onkyo", "KEY_VOLUMEUP")
            except CompoundException:
                logging.error(traceback.format_exc())

        elif a == "k-off":
            logging.info("turning kitchen speakers off")
            try:
                send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
                press_and_hold_to_onkyo(BTN_LEVEL_MINUS, KITCHEN_SPEAKERS_HOLD_TIME)
                send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
                press_and_hold_to_onkyo(BTN_LEVEL_MINUS, KITCHEN_SPEAKERS_HOLD_TIME)
            except CompoundException:
                logging.error(traceback.format_exc())

        elif a == "k-on":
            logging.info("turning kitchen speakers on")
            try:
                send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
                press_and_hold_to_onkyo(BTN_LEVEL_PLUS, KITCHEN_SPEAKERS_HOLD_TIME)
                send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
                send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
                press_and_hold_to_onkyo(BTN_LEVEL_PLUS, KITCHEN_SPEAKERS_HOLD_TIME)
                send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
            except CompoundException:
                logging.error(traceback.format_exc())

        elif a == "disco-off":
            logging.info("turning disco spotlight off")
            try:
                logging.info("a")
            except CompoundException:
                logging.error(traceback.format_exc())

        elif a == "disco-on":
            logging.info("turning disco spotlight on")
            try:
                logging.info("a")
            except CompoundException:
                logging.error(traceback.format_exc())
