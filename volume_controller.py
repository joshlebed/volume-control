"""
docstring
"""


from ratelimit import limits
import json
import sys
import signal
import time
import requests
import argparse
import keyboard

BASE_URL = "https://api.switch-bot.com/"


def get_auth_header(auth_token):
    return {
        "Authorization": auth_token,
    }


def get_config(file_path):
    try:
        with open(file_path) as auth_file:
            config = json.load(auth_file)
            return {"switchbot_auth": config["switchbot_auth"]}
    except:
        return False


def print_response(response):
    print(json.dumps(json.loads(response.text), indent=2))


class SwitchBotAPI(object):
    def __init__(self, switchbot_auth):
        self.switchbot_auth = switchbot_auth

    def get_devices(self):
        get_devices_url = BASE_URL + "v1.0/devices"
        response = requests.get(
            get_devices_url, headers=get_auth_header(self.switchbot_auth)
        )
        print_response(response)

    def get_receiver_status(self):
        receiver_remote_id = "02-202110301641-53087952"
        get_receiver_status_url = (
            BASE_URL + "v1.0/devices/" + receiver_remote_id + "/status"
        )
        print(get_receiver_status_url)
        response = requests.get(
            get_receiver_status_url, headers=get_auth_header(self.switchbot_auth)
        )
        print_response(response)

    @limits(calls=1, period=1)
    def send_receiver_command(self, command):
        receiver_remote_id = "02-202110301641-53087952"
        post_receiver_url = (
            BASE_URL + "v1.0/devices/" + receiver_remote_id + "/commands"
        )
        body = {
            "command": command,
            "parameter": "default",
            "commandType": "customize",
        }
        print(post_receiver_url)
        response = requests.post(
            post_receiver_url,
            headers=get_auth_header(self.switchbot_auth),
            json=body,
        )
        print_response(response)
        print("sent")

    def send_volume_down(self):
        self.send_receiver_command("volume_down")

    def send_volume_up(self):
        self.send_receiver_command("volume_up")

    def send_receiver_power(self):
        self.send_receiver_command("power")


class KeyListener(object):
    def __init__(self, switchbot_auth):
        self.done = False
        self.d_switchBotApi = SwitchBotAPI(switchbot_auth)
        signal.signal(signal.SIGINT, self.cleanup)
        keyboard.hook(self.my_on_key_event)
        while not self.done:
            time.sleep(1)  #  Wait for Ctrl+C

    def cleanup(self, signum, frame):
        self.done = True

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
                print("mute")
            elif e.scan_code == 114:
                print("vol down")
                try:
                    self.d_switchBotApi.send_volume_down()
                except:
                    print("hit limit")
            elif e.scan_code == 115:
                print("vol up")
                try:
                    self.d_switchBotApi.send_volume_up()
                except:
                    print("hit limit")


def main():
    parser = argparse.ArgumentParser(
        description="listen for volume keys, control volume"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="path to config.json",
    )
    args = parser.parse_args()
    config_path = args.config
    config = get_config(config_path)
    if not config:
        print("invalid config, exiting")
        return

    key_listener = KeyListener(config["switchbot_auth"])


if __name__ == "__main__":
    main()
