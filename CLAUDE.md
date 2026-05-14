read @README.md for high level context on the repo.

# agent notes for volume-control

Cross-cutting infra docs (network, hosts, dev workflow, safety rails) live in
the sibling [`homelab`](https://github.com/joshlebed/homelab) repo.
If `~/code/homelab` (or `/home/pi/code/homelab` on the Pi) doesn't
exist, clone it:

```bash
git clone git@github.com:joshlebed/homelab.git ../homelab
```

## deployed on

`pi`, as the `volume_control.service` systemd unit (runs as user `pi`). Reads
raw input from a USB numpad/macropad in `/dev/input/`, translates each keypress
into one of three downstream actions:

1. **IR commands** via LIRC → Onkyo receiver, Roku TV
2. **WebSocket commands** → QLC+ daemon on `mediaserver:9999` (consumes the
   `qlcplus` package from the sibling `qlc-config` repo)
3. **HTTP commands** → Home Assistant on `pi:8123` (e.g. disco-ball motor)

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
   `mediaserver:9999`. If lights stop responding, check the QLC+ service on
   mediaserver before suspecting this repo
   (`ssh mediaserver "systemctl status qlcplus"`).

4. **Hold-to-repeat keys** (volume up/down) use a different code path than
   press-to-toggle keys. Watch for race conditions when refactoring
   `coordinator.py`.

## production-critical reminder

This service is the primary AV interface in the home — when it's broken, nobody
can change the volume or switch inputs without finding a phone/laptop. See
`../homelab/CLAUDE.md` for the full safety-rail policy. Before pushing
changes that affect button mappings or service startup, `make debug` locally on
the Pi.
