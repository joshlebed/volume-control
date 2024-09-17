# volume-control

python service to send IR commands to AV receiver and other IR devices based on keyboard input

## keyboard media controller script

### buttons:

#### OG 6 button wired macropad

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

#### wireless numpad

```
ESC| X |TAB| =
---┼---┼---┼---
NUM| / | * |<-
---┼---┼---┼---
 7 | 8 | 9 | -
---┼---┼---┼---
 4 | 5 | 6 | +
---┼---┼---┼---
 1 | 2 | 3 |
---┴---┼---┤RET
   0   | . |

[not implemented yet]

ESC - cancel current command (TODO)
X - can't remap this button
TAB - spotify dark mode (TODO)
= - turn TV off (TODO)
NUM -
/ -
* -
<- - disco light white
7 -
8 -
9 -
- - disco light yellow
4 - DJ mode
5 - TV mode
6 -
+ - disco light red
1 - volume down
2 - volume up
3 -
0 -
. -
RET - disco light on/off
```

### quickstart

start in background

```bash
nohup python3.11 ~/code/volume-control/scripts/volume_control.py &> /tmp/nohup.out & disown
```

watch the logs

```bash
tail -f /tmp/volume_controller.log
```

### terminal aliases

add this line to your `.zshrc` or `.bashrc` to get some useful aliases:

```bash
source [PATH_TO_THIS_REPO]/scripts/shell-aliases.sh
source /home/pi/code/volume-control/scripts/shell-aliases.sh
```

### run in foreground for debugging

```bash
python3 ~/code/volume-control/scripts/volume_control.py
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

## keylogger info

https://github.com/kernc/logkeys
`sudo logkeys --start --output test.log --device event4`
`sudo logkeys --start --device event4`
`python3 ~/code/volume-control/volume_control.py`

IR emitter module pinout:
VCC goes to 5v power - green -> brown
DAT goes to GPIO 18 (data) - orange -> grey
GND goes to ground - yellow -> white

TODO:

- better docs on how LIRC is used and configured here
- how do I get new codes from a remote?

## LIRC notes

### general notes

this looks like a good guide:
https://stackoverflow.com/questions/57437261/setup-ir-remote-control-using-lirc-for-the-raspberry-pi-rpi

this is also a pretty good guide:
https://www.instructables.com/Setup-IR-Remote-Control-Using-LIRC-for-the-Raspber/

## terminal volume commands

```bash
irsend SEND_ONCE onkyo KEY_VOLUMEUP
irsend SEND_ONCE onkyo KEY_VOLUMEDOWN
```

## debugging ir emitter

- check this: `sudo vi /boot/config.txt` - it should be

### adding new IR codes workflow:

- https://www.lirc.org/html/configuration-guide.html#appendix-10
- https://raspberrypi.stackexchange.com/questions/104008/lirc-irrecord-wont-record-buster-mode2-works

for a new device, you'll need to follow this guide to tweak some config settings and get LIRC working

- https://stackoverflow.com/questions/57437261/setup-ir-remote-control-using-lirc-for-the-raspberry-pi-rpi

#### edit the boot config to switch from transmit to receive

```bash
sudo vim /boot/config.txt
```

near the end, find this (or add it if it's not there):

```conf
# this line should be uncommented for receiver to work
dtoverlay=gpio-ir,gpio_pin=17
# this line should be uncommented for transmitter to work
dtoverlay=gpio-ir-tx,gpio_pin=18
```

then check the config:

```bash
sudo systemctl stop lircd.service
sudo systemctl start lircd.service
sudo systemctl status lircd.service
```

and reboot

```bash
sudo reboot
```

#### record codes

stop LIRCD if it's running:

```bash
sudo systemctl stop lircd.service
```

then use irrecord to create a remote config:

```bash
sudo irrecord -u -n -d /dev/lirc[probably 0 or 1] ~/code/[remote_name].lircd.conf
```

add those remote codes to this repo in `remotes/*.lird.conf`, then copy to the
`/etc/lirc/lircd.conf.d/` dir so they get picked up by LIRCD. then restart LIRCD:

```bash
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

figure out how to apply `automated-commands.cron`, and add instructions to README
