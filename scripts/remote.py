import asyncio
import time
import traceback
from enum import Enum, StrEnum

import lirc
from lirc.exceptions import (
    LircdCommandFailureError,
    LircdConnectionError,
    LircdInvalidReplyPacketError,
    LircdSocketError,
    LircError,
    UnsupportedOperatingSystemError,
)

from scripts.logger import logger


class RemoteID(StrEnum):
    ONKYO = "onkyo"
    ROKU = "roku"
    DISCO_LIGHT = "ADJ-REMOTE"


class OnkyoButton(StrEnum):
    KEY_POWER = "KEY_POWER"
    BTN_1 = "BTN_1"
    GOTO_TV_INPUT = "BTN_1"
    BTN_2 = "BTN_2"
    GOTO_DJ_INPUT = "BTN_2"
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
    POWER = "POWER"
    HOME = "HOME"
    BACK = "BACK"
    UP = "UP"
    PLAY_PAUSE = "PLAY_PAUSE"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    DOWN = "DOWN"
    OK = "OK"
    BACK_A_LITTLE_BIT = "BACK_A_LITTLE_BIT"
    STAR = "STAR"
    REWIND = "REWIND"
    FAST_FORWARD = "FAST_FORWARD"
    BUTTON_1 = "BUTTON_1"
    BUTTON_2 = "BUTTON_2"
    NETFLIX = "NETFLIX"
    DISNEY_PLUS = "DISNEY_PLUS"
    APPLE_TV = "APPLE_TV"
    PARAMOUNT_PLUS = "PARAMOUNT_PLUS"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    MUTE = "MUTE"


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

    # new below this line --------------

    async def send_to_remote_async(self, remote_id, msg):
        try:
            await self.client.send_once(remote_id, msg)
        except CompoundException:
            logger.error(traceback.format_exc())

    async def send_to_remote_then_sleep_async(self, remote_id, msg):
        await self.send_to_remote_async(remote_id, msg)
        await asyncio.sleep(2.0)

    # old below this line --------------

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
    def switch_to_dj_mode_and_reset_volume_accordingly_LEGACY(self):
        logger.info("switching to dj mode (LEGACY)")

        self.receiver_input_source = ReceiverInputSource.DJ

        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEDOWN, HoldTime.VOLUME_ALL_THE_WAY.value
        )
        self.send_to_onkyo_then_sleep(OnkyoButton.GOTO_DJ_INPUT)
        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEUP, HoldTime.VOLUME_0_TO_60.value
        )

        logger.info("done switching to dj mode (LEGACY)")

    def switch_to_tv_mode_and_reset_volume_accordingly_LEGACY(self):
        logger.info("switching to tv mode (LEGACY)")

        self.receiver_input_source = ReceiverInputSource.TV

        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEDOWN, HoldTime.VOLUME_ALL_THE_WAY.value
        )
        self.send_to_onkyo_then_sleep(OnkyoButton.GOTO_TV_INPUT)
        self.press_and_hold_to_onkyo(
            OnkyoButton.KEY_VOLUMEUP, HoldTime.VOLUME_0_TO_30.value
        )

        logger.info("done switching to tv mode (LEGACY)")

    def switch_to_dj_mode(self):
        logger.info("switching to dj mode")
        self.receiver_input_source = ReceiverInputSource.DJ
        self.send_to_onkyo_then_sleep(OnkyoButton.GOTO_DJ_INPUT)
        logger.info("done switching to dj mode")

    def switch_to_tv_mode(self):
        logger.info("switching to tv mode")
        self.receiver_input_source = ReceiverInputSource.TV
        self.send_to_onkyo_then_sleep(OnkyoButton.GOTO_TV_INPUT)
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
        self.kitchen_speakers_on = False

        self.clear_menu_state()
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 5)
        self.press_and_hold_to_onkyo(
            OnkyoButton.BTN_LEVEL_MINUS, HoldTime.KITCHEN_SPEAKERS.value
        )
        self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 1)
        self.press_and_hold_to_onkyo(
            OnkyoButton.BTN_LEVEL_MINUS, HoldTime.KITCHEN_SPEAKERS.value
        )

        logger.info("done turning kitchen speakers off")

    def turn_kitchen_speakers_on(self):
        logger.info("turning kitchen speakers on")
        self.kitchen_speakers_on = True

        self.clear_menu_state()
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
        if not self.kitchen_speakers_on:
            self.turn_kitchen_speakers_on()
        else:
            self.turn_kitchen_speakers_off()

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

    def toggle_spotify_dark_mode(self):
        logger.info("toggling spotify dark mode")
        self.send_to_roku_then_sleep(RokuButton.RIGHT, 6)
        self.send_to_roku_then_sleep(RokuButton.OK)
        self.send_to_roku_then_sleep(RokuButton.BACK)

    def toggle_tv_power(self):
        logger.info("toggling TV power")
        self.send_to_roku_then_sleep(RokuButton.POWER)
