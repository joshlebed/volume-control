"""Tests for per-device input supervision.

Two layers:

* Unit tests drive ``supervise_device`` with fake devices/openers. They need
  only the stdlib (no evdev, no lirc, no hardware) so they run on any platform,
  including the dev laptop, and are the fast iteration loop.
* An integration test builds *real* virtual keyboards with ``evdev.UInput`` and
  exercises the real ``async_read_loop`` + real ENODEV-on-disconnect path. It
  auto-skips unless ``/dev/uinput`` is writable (i.e. run as root on Linux:
  ``sudo make test`` on the Pi).

The headline behavior under test is the bug this module was written to fix:
one keypad being disconnected must not stop another.
"""

import asyncio
import os

import pytest

from device_supervisor import supervise_device

EV_KEY = 1  # evdev.ecodes.ecodes["EV_KEY"]; hardcoded so unit tests need no evdev


# --------------------------------------------------------------------------- #
# fakes / helpers
# --------------------------------------------------------------------------- #
class Ev:
    """Minimal stand-in for an evdev input event."""

    def __init__(self, type, code, value):
        self.type = type
        self.code = code
        self.value = value


class FakeDevice:
    """Async-iterable fake input device.

    Yields ``events`` in order, then (optionally) raises ``raise_after`` to
    simulate a mid-read disconnect. Records whether it was closed.
    """

    def __init__(self, events=(), raise_after=None):
        self._events = list(events)
        self._raise_after = raise_after
        self.closed = False

    async def async_read_loop(self):
        for event in self._events:
            yield event
        if self._raise_after is not None:
            raise self._raise_after

    def close(self):
        self.closed = True


def make_opener(*items):
    """Build an ``open_device`` callable that returns/raises ``items`` in order.

    Each item is either a ``FakeDevice`` (returned) or an exception instance
    (raised on that call). Once exhausted, subsequent opens raise
    ``FileNotFoundError`` -- i.e. the device is treated as permanently absent.
    """
    seq = list(items)

    def _open():
        if not seq:
            raise FileNotFoundError("device absent")
        item = seq.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    return _open


def bounded(n):
    """A ``running`` predicate that returns True ``n`` times, then False."""
    state = {"n": n}

    def _pred():
        if state["n"] <= 0:
            return False
        state["n"] -= 1
        return True

    return _pred


async def _noop_sleep(_seconds):
    # Don't actually wait, but yield control so other tasks make progress.
    await asyncio.sleep(0)


def _is_key(event):
    return event.type == EV_KEY


# --------------------------------------------------------------------------- #
# unit tests
# --------------------------------------------------------------------------- #
def test_absent_device_retries_until_present():
    """An absent device backs off and retries; it does not propagate."""
    handled = []
    device = FakeDevice(events=[Ev(EV_KEY, 30, 1)])
    opener = make_opener(FileNotFoundError("gone"), OSError("nope"), device)
    sleeps = []

    async def record_sleep(seconds):
        sleeps.append(seconds)

    asyncio.run(
        supervise_device(
            "kbdA",
            opener,
            lambda e: handled.append((e.code, e.value)),
            is_key_event=_is_key,
            on_lirc_desync=lambda: None,
            retry_seconds=5,
            sleep=record_sleep,
            running=bounded(3),
        )
    )

    assert handled == [(30, 1)]          # event delivered once the device appeared
    assert sleeps == [5, 5, 5]           # two absent backoffs + one post-session
    assert device.closed


def test_disconnect_midread_reopens_same_supervisor():
    """A mid-read ENODEV closes the device and reopens it -- same supervisor."""
    handled = []
    dev1 = FakeDevice(events=[Ev(EV_KEY, 30, 1)], raise_after=OSError(19, "No such device"))
    dev2 = FakeDevice(events=[Ev(EV_KEY, 31, 1)])
    opener = make_opener(dev1, dev2)

    asyncio.run(
        supervise_device(
            "kbdA",
            opener,
            lambda e: handled.append(e.code),
            is_key_event=_is_key,
            on_lirc_desync=lambda: None,
            retry_seconds=1,
            sleep=_noop_sleep,
            running=bounded(2),
        )
    )

    assert handled == [30, 31]           # kept going across the reconnect
    assert dev1.closed and dev2.closed


def test_lirc_desync_recovers_inline_without_dropping_keypad():
    """A TimeoutError from handle_event recreates the lirc client and keeps
    reading the SAME keypad -- it must not be misread as a disconnect.

    If the outer ``except OSError`` wrongly caught the TimeoutError (it's an
    OSError subclass), reading would stop after code 30 and 31 would be lost;
    the ``handled == [30, 31]`` assertion is what pins the except ordering.
    """
    handled = []
    desyncs = []

    def handler(event):
        handled.append(event.code)
        if event.code == 30:
            raise TimeoutError("lircd socket timed out")

    device = FakeDevice(events=[Ev(EV_KEY, 30, 1), Ev(EV_KEY, 31, 1)])

    asyncio.run(
        supervise_device(
            "kbdA",
            make_opener(device),
            handler,
            is_key_event=_is_key,
            on_lirc_desync=lambda: desyncs.append(True),
            retry_seconds=1,
            sleep=_noop_sleep,
            running=bounded(1),
        )
    )

    assert handled == [30, 31]           # kept reading past the timeout
    assert desyncs == [True]             # recreated the client exactly once
    assert device.closed


def test_non_key_events_are_ignored():
    """Events failing is_key_event are not passed to handle_event."""
    handled = []
    device = FakeDevice(events=[Ev(0, 0, 0), Ev(EV_KEY, 42, 1), Ev(4, 4, 4)])

    asyncio.run(
        supervise_device(
            "kbdA",
            make_opener(device),
            lambda e: handled.append(e.code),
            is_key_event=_is_key,
            on_lirc_desync=lambda: None,
            retry_seconds=1,
            sleep=_noop_sleep,
            running=bounded(1),
        )
    )

    assert handled == [42]


def test_one_absent_device_does_not_stop_another():
    """THE headline: two independent supervisors under one TaskGroup. One device
    is absent the entire time; the other must keep delivering events.

    Under the old single-TaskGroup / shared-open design this was impossible --
    the absent device aborted the shared restart and/or cancelled its sibling.
    """
    handled_a = []
    handled_b = []

    opener_a = make_opener()  # always FileNotFoundError -> A never present
    opener_b = make_opener(
        FakeDevice([Ev(EV_KEY, 48, 1)]),
        FakeDevice([Ev(EV_KEY, 48, 0)]),
        FakeDevice([Ev(EV_KEY, 49, 1)]),
    )

    async def run():
        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                supervise_device(
                    "A",
                    opener_a,
                    lambda e: handled_a.append(e.code),
                    is_key_event=_is_key,
                    on_lirc_desync=lambda: None,
                    retry_seconds=0,
                    sleep=_noop_sleep,
                    running=bounded(3),
                )
            )
            tg.create_task(
                supervise_device(
                    "B",
                    opener_b,
                    lambda e: handled_b.append(e.code),
                    is_key_event=_is_key,
                    on_lirc_desync=lambda: None,
                    retry_seconds=0,
                    sleep=_noop_sleep,
                    running=bounded(3),
                )
            )

    asyncio.run(run())

    assert handled_a == []               # A was absent the whole time
    assert handled_b == [48, 48, 49]     # B worked anyway


# --------------------------------------------------------------------------- #
# integration test (real evdev virtual devices) -- needs writable /dev/uinput
# --------------------------------------------------------------------------- #
try:
    import evdev
    from evdev import InputDevice, UInput, ecodes

    _HAVE_EVDEV = True
except Exception:  # pragma: no cover - evdev is Linux-only
    _HAVE_EVDEV = False


def _uinput_ready():
    return (
        _HAVE_EVDEV
        and os.path.exists("/dev/uinput")
        and os.access("/dev/uinput", os.W_OK)
    )


requires_uinput = pytest.mark.skipif(
    not _uinput_ready(),
    reason="needs a writable /dev/uinput (run as root on Linux, e.g. `sudo make test`)",
)


@requires_uinput
def test_real_evdev_unplug_isolation_and_recovery(tmp_path):
    """End-to-end with real evdev: two virtual keyboards, each reached through a
    stable symlink (mimicking a /dev/input/by-id path). Prove that unplugging
    one keypad does not stop the other, and that the unplugged one recovers when
    it comes back.
    """

    async def scenario():
        ev_key = ecodes.EV_KEY
        link_a = str(tmp_path / "kbdA")
        link_b = str(tmp_path / "kbdB")
        got_a = []
        got_b = []
        ui_a = ui_b = ui_a2 = None
        task_a = task_b = None

        def emit(ui, key):
            ui.write(ev_key, key, 1)
            ui.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)
            ui.write(ev_key, key, 0)
            ui.write(ecodes.EV_SYN, ecodes.SYN_REPORT, 0)
            ui.syn()

        try:
            ui_a = UInput({ecodes.EV_KEY: [ecodes.KEY_A]}, name="vc-test-A")
            ui_b = UInput({ecodes.EV_KEY: [ecodes.KEY_B]}, name="vc-test-B")
            os.symlink(ui_a.device.path, link_a)
            os.symlink(ui_b.device.path, link_b)

            task_a = asyncio.create_task(
                supervise_device(
                    link_a,
                    lambda: InputDevice(link_a),
                    lambda e: got_a.append(e.value),
                    is_key_event=lambda e: e.type == ev_key,
                    on_lirc_desync=lambda: None,
                    retry_seconds=0.2,
                )
            )
            task_b = asyncio.create_task(
                supervise_device(
                    link_b,
                    lambda: InputDevice(link_b),
                    lambda e: got_b.append(e.value),
                    is_key_event=lambda e: e.type == ev_key,
                    on_lirc_desync=lambda: None,
                    retry_seconds=0.2,
                )
            )

            await asyncio.sleep(0.5)  # let both supervisors open their devices
            emit(ui_a, ecodes.KEY_A)
            emit(ui_b, ecodes.KEY_B)
            await asyncio.sleep(0.5)
            assert len(got_a) >= 2, "keypad A never delivered events"
            assert len(got_b) >= 2, "keypad B never delivered events"

            # --- unplug A ---
            os.unlink(link_a)
            ui_a.close()
            await asyncio.sleep(0.8)  # A supervisor sees ENODEV, enters retry
            got_b.clear()
            emit(ui_b, ecodes.KEY_B)
            await asyncio.sleep(0.5)
            assert len(got_b) >= 2, "keypad B stopped when A was unplugged (regression!)"

            # --- replug A (fresh device, same stable path) ---
            ui_a2 = UInput({ecodes.EV_KEY: [ecodes.KEY_A]}, name="vc-test-A2")
            os.symlink(ui_a2.device.path, link_a)
            await asyncio.sleep(0.8)  # A supervisor reopens the path
            got_a.clear()
            emit(ui_a2, ecodes.KEY_A)
            await asyncio.sleep(0.5)
            assert len(got_a) >= 2, "keypad A did not recover after replug"
        finally:
            for task in (task_a, task_b):
                if task is not None:
                    task.cancel()
            await asyncio.gather(
                *[t for t in (task_a, task_b) if t is not None],
                return_exceptions=True,
            )
            for ui in (ui_a, ui_b, ui_a2):
                if ui is not None:
                    try:
                        ui.close()
                    except Exception:
                        pass

    asyncio.run(scenario())
