# volume-control

Python service that translates keyboard/numpad input into IR commands (via LIRC) and lighting control (via QLC+) for home AV equipment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Raspberry Pi (this service)                                                │
│                                                                             │
│  USB Numpad/Macropad  ──▶  volume_control.py  ──┬──▶  LIRC  ──▶  IR Blaster │
│                                                 │                           │
│                                                 ├──▶  QLC+ (WebSocket:9999) │
│                                                 │                           │
│                                                 └──▶  Home Assistant (HTTP) │
└─────────────────────────────────────────────────────────────────────────────┘
                                                            │
                              ┌─────────────────────────────┘
                              ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Onkyo Receiver  │  │  Roku TV         │  │  QLC+ Server     │
│  (IR)            │  │  (IR)            │  │  192.168.0.221   │
│                  │  │                  │  │  ↓               │
│  Volume, Input,  │  │  Navigation,     │  │  ADJ Pinspot     │
│  Surround Mode   │  │  Power           │  │  Spotlight       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Operations (Quick Reference)

All common operations are available via `make`. Run `make help` to see all commands.

### Service Management

```bash
make status      # Check if service is running
make restart     # Restart after code changes
make logs        # Tail application logs
make logs-service # Tail systemd journal logs
```

### Development

```bash
make debug       # Stop service and run in foreground
make run         # Run in foreground (without stopping service)
make test-qlc    # Test QLC+ WebSocket connection
```

## Initial Setup

### 1. Create virtual environment and install dependencies

```bash
python3 -m venv .venv
make install
```

### 2. Deploy systemd service

```bash
make deploy      # Copies service file, enables on boot
make start       # Start the service
```

### 3. (Optional) Shell aliases

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export PATH_TO_VOLUME_CONTROL_REPO="/home/pi/code/volume-control"
source "${PATH_TO_VOLUME_CONTROL_REPO}/src/shell-aliases.sh"
```

## Deployment

The service runs as a systemd unit (`volume_control.service`).

| File               | Location                                     |
| ------------------ | -------------------------------------------- |
| Service definition | `src/volume_control.service`                 |
| Installed location | `/etc/systemd/system/volume_control.service` |
| Python venv        | `.venv/`                                     |
| Application logs   | `/tmp/volume_controller.log`                 |

### Deployment workflow

After making changes:

```bash
# Code changes only:
make restart

# Service file changes:
make reload
make restart

# Full redeploy:
make deploy
make restart
```

### Service configuration

The service is configured to:

- Run as user `pi`
- Auto-restart on failure
- Start on boot (via `WantedBy=multi-user.target`)

## Button Mappings

### Wireless Numpad

```
ESC| X |TAB| =         Function:
---┼---┼---┼---
NUM| / | * |<-         TAB = Spotify dark mode
---┼---┼---┼---        =   = TV power toggle
 7 | 8 | 9 | -         <-  = Disco light WHITE
---┼---┼---┼---        7   = Kitchen speakers ON
 4 | 5 | 6 | +         8   = Kitchen speakers OFF
---┼---┼---┼---        -   = Disco light YELLOW
 1 | 2 | 3 |           4   = TV mode
---┴---┼---┤RET        5   = DJ mode
   0   | . |           +   = Disco light RED
                       1   = Volume DOWN (hold)
                       2   = Volume UP (hold)
                       0   = Toggle stereo/direct
                       RET = Disco ball motor toggle
```

### 6-Button Wired Macropad

```
 1 | 2 | 3             1 = Volume UP (hold)
---┼---┼---            2 = Toggle surround mode
 4 | 5 | 6             3 = Toggle DJ/TV mode
                       4 = Volume DOWN (hold)
                       5 = Disco light YELLOW
                       6 = Toggle kitchen speakers
```

## External Dependencies

### QLC+ (Lighting Control)

- **Host:** 192.168.0.221
- **Port:** 9999 (WebSocket)
- **Functions:** off(0), white(1), red(2), yellow(3)
- **Test:** `make test-qlc`

### Home Assistant (Disco Ball Motor)

- **Host:** 192.168.0.181:8123
- **Entity:** `switch.local_disco_ball`

### LIRC (IR Blaster)

Remote configurations in `remotes/`:

- `onkyo.lircd.conf` - Onkyo receiver
- `roku.lircd.conf` - Roku TV
- `ADJ-REMOTE.lircd.conf` - ADJ disco light (legacy)

## Development

### Run in foreground for debugging

```bash
make debug    # Stops service and runs in foreground
```

Or manually:

```bash
make stop
.venv/bin/python src/volume_control.py
```

### Debugging input devices

List available input devices:

```bash
ls /dev/input/by-id/
```

Monitor raw input:

```bash
sudo cat /dev/input/event*
```

### Project structure

```
volume-control/
├── src/
│   ├── volume_control.py      # Main entry point, event loop
│   ├── coordinator.py         # Keyboard event handler
│   ├── remote.py              # IR/QLC+/HTTP command sender
│   ├── logger.py              # Logging configuration
│   ├── requirements.txt       # Python dependencies
│   └── volume_control.service # Systemd service definition
├── remotes/                   # LIRC remote configurations
├── Makefile                   # Common operations
└── README.md
```

## LIRC Configuration

### Test IR commands

```bash
irsend SEND_ONCE onkyo KEY_VOLUMEUP
irsend SEND_ONCE onkyo KEY_VOLUMEDOWN
```

### Boot configuration

Edit `/boot/config.txt`:

```conf
# Receiver (for recording new codes)
dtoverlay=gpio-ir,gpio_pin=17

# Transmitter (normal operation)
dtoverlay=gpio-ir-tx,gpio_pin=18
```

### Recording new IR codes

1. Stop LIRC and switch to receive mode:

   ```bash
   sudo systemctl stop lircd.service
   # Edit /boot/config.txt to enable receiver
   sudo reboot
   ```

2. Record codes:

   ```bash
   sudo irrecord -u -n -d /dev/lirc0 ~/new_remote.lircd.conf
   ```

3. Install the new remote config:

   ```bash
   sudo cp ~/new_remote.lircd.conf /etc/lirc/lircd.conf.d/
   sudo systemctl restart lircd.service
   ```

4. Switch back to transmit mode in `/boot/config.txt` and reboot.

### IR hardware pinout

| Pin | Connection |
| --- | ---------- |
| VCC | 5V power   |
| DAT | GPIO 18    |
| GND | Ground     |

## Troubleshooting

### Service won't start

```bash
make status           # Check service status
make logs-service     # Check systemd logs
make debug            # Run in foreground to see errors
```

### QLC+ connection fails

```bash
make test-qlc         # Test connection
ping 192.168.0.221    # Check network
```

Verify QLC+ is running with WebSocket enabled (`-w` flag).

### Input device not found

```bash
ls /dev/input/by-id/  # List devices
# Update device path in src/volume_control.py if needed
```
