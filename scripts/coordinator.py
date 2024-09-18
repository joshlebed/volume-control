import asyncio

from remote import Remote

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


class Coordinator:
    def __init__(self, remote: Remote):
        print("creating coordinator")
        self.remote = remote
        self.current_task = None

    def handle_keyboard_event(self, event):
        print("handling keyboard event")

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
                self.remote.start_holding_volume_down()

            elif (
                event.code == MACROPAD_VOLUME_UP_TRIGGER
                or event.code == NUMPAD_VOLUME_UP_TRIGGER
            ):
                self.remote.start_holding_volume_up()
            # elif event.code == MACROPAD_TOGGLE_DJ_TV_MODE_TRIGGER:
            #     self.remote.toggle_input_tv_to_dj()
            # elif event.code == MACROPAD_TOGGLE_KITCHEN_SPEAKERS_TRIGGER:
            #     self.remote.toggle_kitchen_speakers()
            elif event.code == NUMPAD_KITCHEN_SPEAKERS_ON_TRIGGER:
                self.current_task = asyncio.create_task(
                    self.remote.turn_kitchen_speakers_on_ASYNC()
                )
            elif event.code == NUMPAD_KITCHEN_SPEAKERS_OFF_TRIGGER:
                self.current_task = asyncio.create_task(
                    self.remote.turn_kitchen_speakers_off_ASYNC()
                )
            elif (
                event.code == MACROPAD_TOGGLE_SURROUND_MODE_TRIGGER
                or event.code == NUMPAD_TOGGLE_SURROUND_MODE_TRIGGER
            ):
                self.remote.toggle_surround_mode()
            elif event.code == MACROPAD_TOGGLE_DISCO_LIGHT_RED_YELLOW_TRIGGER:
                self.remote.toggle_disco_light_red_yellow()
            elif event.code == NUMPAD_DJ_MODE_TRIGGER:
                self.remote.switch_to_dj_mode()
            elif event.code == NUMPAD_TV_MODE_TRIGGER:
                self.remote.switch_to_tv_mode()
            elif event.code == NUMPAD_DISCO_LIGHT_WHITE_TRIGGER:
                self.remote.turn_disco_light_white()
            elif event.code == NUMPAD_DISCO_LIGHT_YELLOW_TRIGGER:
                self.remote.turn_disco_light_yellow()
            elif event.code == NUMPAD_DISCO_LIGHT_RED_TRIGGER:
                self.remote.turn_disco_light_red()
            elif event.code == NUMPAD_DISCO_LIGHT_TOGGLE_TRIGGER:
                self.remote.toggle_disco_light_power()
            elif event.code == NUMPAD_SPOTIFY_DARK_MODE_TRIGGER:
                self.remote.toggle_spotify_dark_mode()
            elif event.code == NUMPAD_TV_POWER_TRIGGER:
                self.remote.toggle_tv_power()

        # release key event
        elif event.value == 0:
            if (
                event.code == MACROPAD_VOLUME_DOWN_TRIGGER
                or event.code == NUMPAD_VOLUME_DOWN_TRIGGER
            ):
                self.remote.stop_holding_volume_button()
                self.remote.stop_holding_volume_button()
                self.remote.stop_holding_volume_button()
            elif (
                event.code == MACROPAD_VOLUME_UP_TRIGGER
                or event.code == NUMPAD_VOLUME_UP_TRIGGER
            ):
                self.remote.stop_holding_volume_button()
