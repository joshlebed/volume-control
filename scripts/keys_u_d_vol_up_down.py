import logging
import time
import traceback
import lirc

client = lirc.Client()

BTN_CH_SEL = "BTN_CH_SEL"
BTN_LEVEL_MINUS = "BTN_LEVEL_MINUS"
BTN_LEVEL_PLUS = "BTN_LEVEL_PLUS"
HOLD_TIME = 3.5


def send_to_onkyo(msg):
    client.send_once("onkyo", msg)


def send_to_onkyo_then_sleep(msg, times=1):
    for _ in range(times):
        send_to_onkyo(msg)
        time.sleep(.2)


def press_and_hold_to_onkyo(msg, seconds=0):
    client.send_start("onkyo", msg)
    time.sleep(seconds)
    client.send_stop("onkyo", msg)
    time.sleep(.2)


while True:
    a = input("next command (u or d): ")
    if a == "d":
        print("vol down")
        try:
            client.send_once("onkyo", "KEY_VOLUMEDOWN")
        except lirc.exceptions.LircdCommandFailureError as error:
            print("Unable to send pause command")
            print(error)  # Error has more info on what lircd sent back.
        except:
            print("unknown error")

    elif a == "u":
        print("vol up")
        try:
            client.send_once("onkyo", "KEY_VOLUMEUP")
        except lirc.exceptions.LircdCommandFailureError as error:
            print("Unable to send pause command")
            print(error)  # Error has more info on what lircd sent back.
        except:
            print("unknown error")

    elif a == "k-off":
        print("turning kitchen speakers off")
        try:
            send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
            press_and_hold_to_onkyo(BTN_LEVEL_MINUS, HOLD_TIME)
            send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
            press_and_hold_to_onkyo(BTN_LEVEL_MINUS, HOLD_TIME)
        except lirc.exceptions.LircdCommandFailureError as error:
            print("Unable to send pause command")
            print(error)  # Error has more info on what lircd sent back.
        except Exception as e:
            logging.error(traceback.format_exc())
            print("unknown error")

    elif a == "k-on":
        print("turning kitchen speakers on")
        try:
            send_to_onkyo_then_sleep(BTN_CH_SEL, 5)
            press_and_hold_to_onkyo(BTN_LEVEL_PLUS, HOLD_TIME)
            send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
            send_to_onkyo_then_sleep(BTN_CH_SEL, 1)
            press_and_hold_to_onkyo(BTN_LEVEL_PLUS, HOLD_TIME)
            send_to_onkyo_then_sleep(BTN_LEVEL_MINUS, 4)
        except lirc.exceptions.LircdCommandFailureError as error:
            print("Unable to send pause command")
            print(error)  # Error has more info on what lircd sent back.
        except Exception as e:
            logging.error(traceback.format_exc())
            print("unknown error")
