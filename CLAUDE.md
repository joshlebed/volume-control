`README.md` is the human-facing overview (what this is, setup, usage); open it when a task needs those details.

# agent notes for volume-control

## deployed on

A Raspberry Pi, as the `volume_control.service` systemd unit (runs as user `pi`). Site settings (QLC+ host, Home Assistant URL/token, disco entity) come from the gitignored `.env` via `EnvironmentFile`; `.env.example` lists them. Reads
raw input from a USB numpad/macropad in `/dev/input/`, translates each keypress
into one of three downstream actions:

1. **IR commands** via LIRC → Onkyo receiver, Roku TV
2. **WebSocket commands** → the QLC+ daemon at `QLCPLUS_HOST:9999` (consumes the
   `qlcplus` package from the sibling `qlc-config` repo)
3. **HTTP commands** → Home Assistant at `HA_BASE_URL` (e.g. disco-ball motor)

## fan-out into other repos

| Downstream     | What we send                   | Where it lives                                                                                     |
| -------------- | ------------------------------ | -------------------------------------------------------------------------------------------------- |
| QLC+           | WebSocket function start/stop  | sibling `qlc-config` repo (provides the `qlcplus` Python client; runs as a service on mediaserver) |
| LIRC remotes   | `irsend` IR pulses             | local `remotes/*.lircd.conf`, copied to `/etc/lirc/lircd.conf.d/`                                  |
| Home Assistant | HTTP `/api/services/...` calls | sibling `home-assistant` repo (defines the entities)                                               |

If a button stops working, suspect order: input device → service → downstream
target. `make logs` first, then `make test-qlc` / `irsend` / `curl` to isolate.

## development

- **Code change**: `make restart` after editing.
- **Service file change**: `make reload && make restart`.
- **Foreground debug**: `make debug` (stops the service, runs in fg with logs to
  stdout).
- **Update qlcplus dep after qlc-config changes**: `make update-qlc`.
- **Run tests**: `make test` (stdlib-only unit tests, run anywhere). On the Pi,
  `sudo make test` additionally runs the real-evdev/uinput integration test
  (needs writable `/dev/uinput`, hence sudo). `make test-deps` installs pytest
  into the venv first if it's missing.

## key gotchas

1. **Input devices need root.** The service runs as `pi`, but reading
   `/dev/input/event*` requires either `input` group membership or running with
   appropriate capabilities. The systemd unit handles this; manual testing under
   a non-root shell will see EACCES.

2. **LIRC boot config is a foot-gun.** `/boot/config.txt` controls whether GPIO
   18 is in transmit (`gpio-ir-tx`) or receive (`gpio-ir`) mode. Recording new
   IR codes requires switching to receive mode and rebooting; forgetting to
   switch back leaves the IR blaster non-functional.

3. **QLC+ dependency lives on a different host.** WebSocket calls go over LAN to
   `QLCPLUS_HOST:9999`. If lights stop responding, check the QLC+ service on
   that host before suspecting this repo (`systemctl status qlcplus` there).

4. **Hold-to-repeat keys** (volume up/down) use a different code path than
   press-to-toggle keys. Watch for race conditions when refactoring
   `coordinator.py`.

5. **The lircd socket can desync.** If a `send_stop()` races lircd's repeat
   handling (lircd logs `busy: repeating` in `journalctl -u lircd`), the
   client's socket goes permanently out of sync — every later lirc command
   times out after 5s while a fresh connection (`irsend`) works fine. Each
   device supervisor now catches that `TimeoutError` inline and recreates the
   connection via `fresh_lirc_client()` without dropping keypad input — no
   restart, no dead window (previously a desync tore down both read loops for
   ~10s). If volume buttons stay dead anyway, `make restart` and check
   `/tmp/volume_controller.log` for repeated `TimeoutError`.

6. **Each keypad is supervised independently — keep it that way.**
   `src/device_supervisor.py` runs one open→read→recover loop per device
   (`supervise_device`), so unplugging one keypad never stops another. The old
   design read both devices as sibling tasks in a single `asyncio.TaskGroup`
   and opened every `evdev.InputDevice()` up front, which coupled their fates:
   `TaskGroup` cancels siblings on the first exception, and one missing device
   raised `FileNotFoundError` that aborted the shared restart — so unplugging
   one keypad killed the other, and the survivor stayed dead until the missing
   one was replugged. Don't refactor the devices back into a shared read loop
   or a single up-front open; that reintroduces the bug. `supervise_device`
   injects its hardware/lirc pieces (imports neither evdev nor lirc), so it's
   unit-testable off-Pi; `sudo make test` on the Pi also runs a real-uinput
   unplug/recovery integration test.

## production-critical reminder

Never commit `.env` or any token: a Home Assistant long-lived token was once
committed to this public repo (revoked 2026-10-23) — that is why everything
site-specific is environment-only now.

This service is the primary AV interface in the home — when it's broken, nobody
can change the volume or switch inputs without finding a phone/laptop. Before pushing
changes that affect button mappings or service startup, `make debug` locally on
the Pi.
