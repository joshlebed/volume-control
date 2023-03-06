# volume-project

raspberry pi python service to change the receiver volume on keyboard input from
USB volume knob

## notes

<!-- TODO: -->

try this:
https://stackoverflow.com/a/49873529/7090159
https://docs.docker.com/storage/
https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipes

other option: ssh in from HASSIO and execute python script

- https://community.home-assistant.io/t/run-command-on-docker-container-from-supervised-hassio/235083/3
- pros and cons?

## usb volume knob service

### quickstart

```bash
python3 ~/code/volume-control/volume_controller_evdev_lirc.py 1>/dev/null 2>/dev/null & disown
tail -f /home/pi/code/pipes/ir-commands-pipe | sh & disown
```

### run in foreground for debugging

```bash
python3 volume_controller_evdev_lirc.py
tail -f /home/pi/code/pipes/ir-commands-pipe | sh
```

### old version

```bash
sudo python3 volume_controller_lirc.py
```

## terminal volume commands

```bash
irsend SEND_ONCE onkyo KEY_VOLUMEUP
irsend SEND_ONCE onkyo KEY_VOLUMEDOWN
```

## keylogger info

https://github.com/kernc/logkeys
`sudo logkeys --start --output test.log --device event4`
`sudo logkeys --start --device event4`
`python3 ~/code/volume-control/volume_controller_evdev_lirc.py`

IR emitter module pinout:
VCC goes to 5v power - green -> brown
DAT goes to GPIO 18 (data) - orange -> grey
GND goes to ground - yellow -> white

TODO:

- better docs on how LIRC is used and configured here
- how do I get new codes from a remote?

## LIRC notes

- https://www.lirc.org/html/configuration-guide.html#appendix-10
- https://raspberrypi.stackexchange.com/questions/104008/lirc-irrecord-wont-record-buster-mode2-works

  - /boot/config.txt
  - see:

  ```
  dtoverlay=gpio-ir,gpio_pin=17
  dtoverlay=gpio-ir-tx,gpio_pin=18
  ```

  - this means the ir receiver is on pin 17, and the transmitter is on pin 18
  - for recording new codes, use irrecord

  ```
  irrecord -u -n -d /dev/lirc1 code/onkyo_GOOD.lircd.conf
  ```

  - add those remote codes in `/etc/lirc/lircd.conf.d/`

  ```
  systemctl restart lircd.service
  ```
