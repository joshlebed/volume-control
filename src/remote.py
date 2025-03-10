import asyncio
import traceback
from enum import Enum, StrEnum

import lirc
import requests

from logger import CompoundException, logger


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


class DiscoLightButton(StrEnum):
    STAND_BY = "STAND_BY"
    FULL_ON = "FULL_ON"
    FADE_GOBO = "FADE_GOBO"
    STROBE = "STROBE"
    COLOR = "COLOR"
    DIMMER_UP = "DIMMER_UP"
    DIMMER_DOWN = "DIMMER_DOWN"
    BUTTON_1 = "1"
    BUTTON_2 = "2"
    BUTTON_3 = "3"
    BUTTON_4 = "4"
    BUTTON_5 = "5"
    BUTTON_6 = "6"
    BUTTON_7 = "7"
    BUTTON_8 = "8"
    BUTTON_9 = "9"
    SHOW_0 = "SHOW_0"
    SOUND_ON = "SOUND_ON"
    SOUND_OFF = "SOUND_OFF"


class HoldTime(Enum):
    KITCHEN_SPEAKERS = 3.5


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
        self.direct_mode = True
        self.is_disco_light_on = False

    # UTILS
    def send_to_remote(self, remote_id, msg):
        try:
            self.client.send_once(remote_id, msg)
        except CompoundException:
            logger.error(traceback.format_exc())

    async def send_to_remote_then_sleep(self, remote_id, msg, times):
        try:
            for _ in range(times):
                self.send_to_remote(remote_id, msg)
                await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            logger.info("send_to_remote_then_sleep was cancelled")

    async def send_to_onkyo_then_sleep(self, msg, times=1):
        await self.send_to_remote_then_sleep(RemoteID.ONKYO, msg, times)

    async def send_to_roku_then_sleep(self, msg, times=1):
        await self.send_to_remote_then_sleep(RemoteID.ROKU, msg, times)

    async def send_to_disco_light_then_sleep(self, msg, times=1):
        await self.send_to_remote_then_sleep(RemoteID.DISCO_LIGHT, msg, times)

    async def press_and_hold_to_onkyo(self, msg, seconds=0):
        try:
            self.client.send_start(RemoteID.ONKYO, msg)
            await asyncio.sleep(seconds)
            self.client.send_stop(RemoteID.ONKYO, msg)
            await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            self.client.send_stop(RemoteID.ONKYO, msg)
            logger.info("press_and_hold_to_onkyo was cancelled")

    # VOLUME CONTROLS
    def start_holding_volume_down(self):
        logger.info("volume down")
        self.client.send_start(RemoteID.ONKYO, OnkyoButton.KEY_VOLUMEDOWN)

    def start_holding_volume_up(self):
        logger.info("volume up")
        self.client.send_start(RemoteID.ONKYO, OnkyoButton.KEY_VOLUMEUP)

    def stop_holding_volume_button(self):
        logger.info("done with volume buttons")
        self.client.send_stop()

    # RECEIVER INPUT
    async def switch_to_dj_mode(self):
        logger.info("switching to dj mode")
        await self.send_to_onkyo_then_sleep(OnkyoButton.GOTO_DJ_INPUT)
        logger.info("done switching to dj mode")

    async def switch_to_tv_mode(self):
        logger.info("switching to tv mode")
        await self.send_to_onkyo_then_sleep(OnkyoButton.GOTO_TV_INPUT)
        logger.info("done switching to tv mode")

    # KITCHEN SPEAKERS
    async def turn_kitchen_speakers_off(self):
        logger.info("turning kitchen speakers off")

        try:
            await self.clear_menu_state()
            await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 5)
            await self.press_and_hold_to_onkyo(
                OnkyoButton.BTN_LEVEL_MINUS, HoldTime.KITCHEN_SPEAKERS.value
            )
            await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 1)
            await self.press_and_hold_to_onkyo(
                OnkyoButton.BTN_LEVEL_MINUS, HoldTime.KITCHEN_SPEAKERS.value
            )
            await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LEVEL_MINUS, 4)

        except asyncio.CancelledError:
            logger.info("turn_kitchen_speakers_off was cancelled")

        logger.info("done turning kitchen speakers off")

    async def turn_kitchen_speakers_on(self):
        logger.info("turning kitchen speakers on")

        try:
            await self.clear_menu_state()
            await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 5)
            await self.press_and_hold_to_onkyo(
                OnkyoButton.BTN_LEVEL_PLUS, HoldTime.KITCHEN_SPEAKERS.value
            )
            await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LEVEL_MINUS, 4)
            await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_CH_SEL, 1)
            await self.press_and_hold_to_onkyo(
                OnkyoButton.BTN_LEVEL_PLUS, HoldTime.KITCHEN_SPEAKERS.value
            )
            await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LEVEL_MINUS, 4)

        except asyncio.CancelledError:
            logger.info("turn_kitchen_speakers_on was cancelled")

        logger.info("done turning kitchen speakers on")

    async def clear_menu_state(self):
        logger.info("clearing menu state async")
        await self.send_to_onkyo_then_sleep(OnkyoButton.KEY_SETUP, 2)

    # SURROUND SOUND MODE
    async def switch_to_all_channel_stereo(self):
        logger.info("switching to all channel stereo")
        await self.send_to_onkyo_then_sleep(OnkyoButton.STEREO)
        await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LISTENINGMODE_LEFT, 4)
        logger.info("done switching to all channel stereo")

    async def switch_to_direct(self):
        logger.info("switching to direct")
        await self.send_to_onkyo_then_sleep(OnkyoButton.STEREO)
        await self.send_to_onkyo_then_sleep(OnkyoButton.BTN_LISTENINGMODE_LEFT)
        logger.info("done switching to direct")

    async def toggle_surround_mode(self):
        logger.info("toggling surround mode between all channel stereo and direct")

        await self.clear_menu_state()

        if not self.direct_mode:
            await self.switch_to_direct()
            self.direct_mode = True

        else:
            await self.switch_to_all_channel_stereo()
            self.direct_mode = False

    # DISCO LIGHT CONTROLS
    async def turn_disco_light_white(self):
        logger.info("turning disco light to single color white mode")
        await self.send_to_disco_light_then_sleep(DiscoLightButton.COLOR)
        await self.send_to_disco_light_then_sleep(DiscoLightButton.BUTTON_9)
        logger.info("done turning disco light to single color yellow mode")

    async def turn_disco_light_yellow(self):
        logger.info("turning disco light to single color yellow mode")
        await self.send_to_disco_light_then_sleep(DiscoLightButton.COLOR)
        await self.send_to_disco_light_then_sleep(DiscoLightButton.BUTTON_2)
        logger.info("done turning disco light to single color yellow mode")

    async def turn_disco_light_red(self):
        logger.info("turning disco light to single color red mode")
        await self.send_to_disco_light_then_sleep(DiscoLightButton.COLOR)
        await self.send_to_disco_light_then_sleep(DiscoLightButton.BUTTON_1)
        logger.info("done turning disco light to single color red mode")

    async def toggle_disco_light_power(self):
        logger.info("toggling disco spotlight power on/off")
        url = "http://192.168.0.181:8123/api/services/switch/toggle"
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhOWE5YmVkMDQ5YTY0MjUxOGY0OTc1ZTYzMTIxNjA3NCIsImlhdCI6MTY2NjA3MDIyMSwiZXhwIjoxOTgxNDMwMjIxfQ.Dz_oPS2tIup2PB89bi6SFAZHxortQh3kZ5hrw-gWdu4"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        data = {"entity_id": "switch.local_disco_ball"}
        requests.post(url, headers=headers, json=data)
        await self.send_to_disco_light_then_sleep(DiscoLightButton.STAND_BY)
        await self.send_to_disco_light_then_sleep(DiscoLightButton.SOUND_OFF)

    async def toggle_disco_light_fade(self):
        logger.info("toggling disco light fade")
        await self.send_to_disco_light_then_sleep(DiscoLightButton.FADE_GOBO)

    async def toggle_spotify_dark_mode(self):
        logger.info("toggling spotify dark mode")
        await self.send_to_roku_then_sleep(RokuButton.LEFT)
        await asyncio.sleep(3)
        await self.send_to_roku_then_sleep(RokuButton.DOWN)
        await self.send_to_roku_then_sleep(RokuButton.LEFT, 2)
        await self.send_to_roku_then_sleep(RokuButton.OK)
        await self.send_to_roku_then_sleep(RokuButton.BACK)

    async def toggle_tv_power(self):
        logger.info("toggling TV power")
        await self.send_to_roku_then_sleep(RokuButton.POWER)

    async def pause(self):
        logger.info("pausing tv")
        await self.send_to_roku_then_sleep(RokuButton.PLAY_PAUSE)
