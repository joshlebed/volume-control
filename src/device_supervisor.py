"""Per-device input supervision.

Each physical keypad gets its own independent open -> read -> recover loop so
that a disconnect (or a lircd desync) on one device never disturbs another.

Why this exists
---------------
Historically both keypads were read as sibling tasks inside a single
``asyncio.TaskGroup``, and every device was (re)opened all-at-once at the top
of one shared retry loop. That coupled their fates in two ways:

* ``asyncio.TaskGroup`` cancels *every* sibling task the moment one child task
  raises a non-``CancelledError`` exception. Unplugging one keypad makes its
  ``async_read_loop`` raise ``OSError``/ENODEV, which instantly cancelled the
  other keypad's task.
* The shared retry loop constructed an ``InputDevice`` for *every* configured
  path before any reading started. A single missing device therefore raised
  ``FileNotFoundError`` and aborted the restart for all of them -- the survivor
  stayed dead until the missing keypad was physically replugged.

``supervise_device`` isolates one device end to end. It deliberately imports
neither ``evdev`` nor ``lirc``: the hardware- and protocol-specific pieces are
injected by the caller, which keeps this control flow unit-testable on any
platform (no Linux input stack or IR daemon required).
"""

import asyncio
import logging

# Reuse the app's configured logger without importing logger.py (which pulls in
# lirc). getLogger("root") returns the same logger instance the app configures.
logger = logging.getLogger("root")


async def supervise_device(
    name,
    open_device,
    handle_event,
    *,
    is_key_event,
    on_lirc_desync,
    retry_seconds,
    sleep=asyncio.sleep,
    running=None,
):
    """Own one input device: (re)open it, read its events, and recover from its
    own failures -- without ever disturbing another device's supervisor.

    Parameters
    ----------
    name:
        Human-readable identifier for logs (e.g. the ``/dev/input/by-id`` path).
    open_device:
        Zero-arg callable returning a freshly-opened device. The device must
        expose ``async_read_loop()`` (an async iterator of events) and
        ``close()``. Raising ``FileNotFoundError``/``OSError`` means "not
        present right now" and triggers a wait-and-retry rather than
        propagating -- this is the normal state while the keypad is unplugged.
    handle_event:
        Callable invoked with each event for which ``is_key_event`` is true. May
        raise ``TimeoutError`` when the lircd socket has desynced (handled via
        ``on_lirc_desync``).
    is_key_event:
        Predicate deciding whether an event should be passed to ``handle_event``.
    on_lirc_desync:
        Zero-arg callback invoked when ``handle_event`` raises ``TimeoutError``.
        Expected to recreate the poisoned lircd connection. Reading then
        continues on the *same* device -- a downstream IR hiccup must not drop
        keypad input.
    retry_seconds:
        Backoff between (re)open attempts.
    sleep:
        Injectable ``asyncio.sleep`` (tests pass a no-op).
    running:
        Optional zero-arg predicate; the supervisor loops while it returns
        ``True``. Defaults to looping forever. Tests pass a bounded predicate so
        the coroutine terminates.

    Note
    ----
    ``TimeoutError`` is a subclass of ``OSError``, so the inner
    ``except TimeoutError`` (lircd desync -> recreate client, keep reading) is
    deliberately nested *inside* and evaluated *before* the outer
    ``except OSError`` (device disconnect -> reopen). Do not flatten these or a
    lircd timeout will be misread as an unplug.
    """
    while running is None or running():
        try:
            device = open_device()
        except (FileNotFoundError, OSError) as exc:
            logger.info(
                "%s not available (%s); retrying in %ss", name, exc, retry_seconds
            )
            await sleep(retry_seconds)
            continue

        logger.info("listening on %s", name)
        try:
            async for event in device.async_read_loop():
                if is_key_event(event):
                    try:
                        handle_event(event)
                    except TimeoutError:
                        logger.info("%s: lircd desync; recreating client", name)
                        on_lirc_desync()
        except OSError as exc:
            # Device disconnected mid-read (ENODEV). Fall through to reopen; every
            # other keypad's supervisor keeps running, untouched.
            logger.info(
                "%s disconnected (%s); will reopen when it returns", name, exc
            )
        finally:
            _safe_close(device, name)

        await sleep(retry_seconds)


def _safe_close(device, name):
    try:
        device.close()
    except Exception:
        logger.info("%s: error closing device, continuing", name)
