"""
docstring
"""


import argparse
import json
import signal
import sys
import time

import keyboard
import lirc
import requests
from ratelimit import exception, limits

client = lirc.Client()
TARGET = "onkyo"


class KeyListener(object):
    def __init__(self):
        self.client = lirc.Client()
        self.done = False
        signal.signal(signal.SIGINT, self.cleanup)
        keyboard.hook(self.my_on_key_event)
        while not self.done:
            time.sleep(1)  #  Wait for Ctrl+C

    def cleanup(self, signum, frame):
        self.done = True

    @limits(calls=1, period=0.2)
    def rate_limited_send_ir_command(self, command):
        client.send_once(TARGET, command)

    def send_ir_command(self, command):
        try:
            self.rate_limited_send_ir_command(command)
        except exception.RateLimitException as error:
            print(error)  # Error has more info on what lircd sent back.

    def my_on_key_event(self, e):
        # print(dir(e))
        # print(e.to_json())
        # 113 is mute
        # 114 is vol down
        # 115 is vol up
        if e.event_type == "down":
            # print("Got key release event: " + str(e))
            # print(f"e.event_type? {e.event_type}")
            # print(f'e.event_type == "down"? {e.event_type == "down"}')

            if e.scan_code == 113:
                print("pause")
                try:
                    # print("trying")
                    self.send_ir_command("KEY_PAUSE")
                except lirc.exceptions.LircdCommandFailureError as error:
                    print("Unable to send pause command")
                    print(error)  # Error has more info on what lircd sent back.
                except:
                    print("unknown error")

            elif e.scan_code == 114:
                print("vol down")
                try:
                    # print("trying")
                    self.send_ir_command("KEY_VOLUMEDOWN")
                except lirc.exceptions.LircdCommandFailureError as error:
                    print("Unable to send volume down command")
                    print(error)  # Error has more info on what lircd sent back.
                except:
                    print("unknown error")
            elif e.scan_code == 115:
                print("vol up")
                try:
                    # print("trying")
                    self.send_ir_command("KEY_VOLUMEUP")
                except lirc.exceptions.LircdCommandFailureError as error:
                    print("Unable to send pause command")
                    print(error)  # Error has more info on what lircd sent back.
                except:
                    print("unknown error")


def main():
    key_listener = KeyListener()


if __name__ == "__main__":
    main()
