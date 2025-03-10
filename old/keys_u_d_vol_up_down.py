import logging
import time
import traceback

import lirc
from logger import CompoundException

client = lirc.Client()

BTN_CH_SEL = "BTN_CH_SEL"
BTN_LEVEL_MINUS = "BTN_LEVEL_MINUS"
BTN_LEVEL_PLUS = "BTN_LEVEL_PLUS"
HOLD_TIME = 3.5
ONKYO_REMOTE_ID = "onkyo"
DISCO_LIGHT_REMOTE_ID = "ADJ-REMOTE"


def send_to_remote(remote_id, msg):
    client.send_once(remote_id, msg)


def send_to_onkyo_then_sleep(msg, times=1):
    for _ in range(times):
        send_to_remote(ONKYO_REMOTE_ID, msg)
        time.sleep(0.2)


def press_and_hold_to_onkyo(msg, seconds=0):
    client.send_start(ONKYO_REMOTE_ID, msg)
    time.sleep(seconds)
    client.send_stop(ONKYO_REMOTE_ID, msg)
    time.sleep(0.2)


while True:
    a = input("next command (u or d): ")
    if a == "d":
        print("vol down")
        try:
            client.send_once("onkyo", "KEY_VOLUMEDOWN")
        except CompoundException:
            logging.error(traceback.format_exc())

    elif a == "u":
        print("vol up")
        try:
            client.send_once("onkyo", "KEY_VOLUMEUP")
        except CompoundException:
            logging.error(traceback.format_exc())

    elif a == "k-off":
        print("turning kitchen speakers off")
        try:
            send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
            press_and_hold_to_onkyo(BTN_LEVEL_MINUS, HOLD_TIME)
            send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
            press_and_hold_to_onkyo(BTN_LEVEL_MINUS, HOLD_TIME)
        except CompoundException:
            logging.error(traceback.format_exc())

    elif a == "k-on":
        print("turning kitchen speakers on")
        try:
            send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
            press_and_hold_to_onkyo(BTN_LEVEL_PLUS, HOLD_TIME)
            send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
            send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
            press_and_hold_to_onkyo(BTN_LEVEL_PLUS, HOLD_TIME)
            send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
        except CompoundException:
            logging.error(traceback.format_exc())

    elif a == "disco-off":
        print("turning disco spotlight off")
        try:
            print("a")
        except CompoundException:
            logging.error(traceback.format_exc())

    elif a == "disco-on":
        print("turning disco spotlight on")
        try:
            print("a")
        except CompoundException:
            logging.error(traceback.format_exc())
