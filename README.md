# volume-control

python service to send IR commands to AV receiver and other IR devices based on keyboard input

## keyboard media controller script

### buttons:

```
 1 | 2 | 3
---┼---┼---
 4 | 5 | 6

1 - vol up
2 - toggle sound mode: all channel stereo vs direct
3 - toggle input: dj mode vs tv mode
4 - vol down
5 - yellow disco light
6 - toggle kitchen speakers: on vs off
```

### quickstart

```bash
nohup python3 ~/code/volume-control/scripts/volume_controller_evdev_lirc.py & disown
```

### run in foreground for debugging

```bash
python3 ~/code/volume-control/scripts/volume_controller_evdev_lirc.py
tail -f /home/pi/code/pipes/ir-commands-pipe | sh     # what is this line doing
```

### debugging input devices

look in `/dev/input/by-id`
get inputs with:

```bash
sudo cat /dev/input/*
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

### adding new IR codes workflow:

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

## notes

<!-- TODO: -->

- FOR NETWORKING: https://community.home-assistant.io/t/remote-access-with-docker/314345

try this:
https://stackoverflow.com/a/49873529/7090159
https://docs.docker.com/storage/
https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipes

other option: ssh in from HASSIO and execute python script

- https://community.home-assistant.io/t/run-command-on-docker-container-from-supervised-hassio/235083/3
- pros and cons?
