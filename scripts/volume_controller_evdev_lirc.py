"""
docstring
"""


import argparse
import json
import signal
import sys
import time

import evdev
import keyboard
import lirc
import requests
from ratelimit import exception, limits

# LIRC
client = lirc.Client()
TARGET = "onkyo"


@limits(calls=1, period=0.2)
def rate_limited_send_ir_command(command):
    client.send_once(TARGET, command)


def send_ir_command(command):
    try:
        rate_limited_send_ir_command(command)
    except lirc.exceptions.LircdCommandFailureError as error:
        print(f"Unable to send command: {command}. error message: {str(error)}")
    except exception.RateLimitException as error:
        print(f"hit rate limit! error: {str(error)}")


def main():
    device = evdev.InputDevice("/dev/input/event2")
    print(device)

    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY and event.value == 1:
            print(evdev.categorize(event))
            print(event.code)
            if event.code == 113:
                print("mute")
                send_ir_command("KEY_PAUSE")
            if event.code == 114:
                print("down")
                send_ir_command("KEY_VOLUMEDOWN")
            if event.code == 115:
                print("up")
                send_ir_command("KEY_VOLUMEUP")


if __name__ == "__main__":
    main()
