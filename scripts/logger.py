import logging
from logging.handlers import RotatingFileHandler

from lirc.exceptions import (
    LircdCommandFailureError,
    LircdConnectionError,
    LircdInvalidReplyPacketError,
    LircdSocketError,
    LircError,
    UnsupportedOperatingSystemError,
)

CompoundException = (
    LircError,
    LircdSocketError,
    LircdConnectionError,
    LircdInvalidReplyPacketError,
    LircdCommandFailureError,
    UnsupportedOperatingSystemError,
)

LOG_FILE = "/tmp/volume_controller.log"
MY_HANDLER = RotatingFileHandler(
    LOG_FILE, mode="a", maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None, delay=0
)
MY_HANDLER.setLevel(logging.DEBUG)
logger = logging.getLogger("root")
logger.setLevel(logging.DEBUG)
logger.addHandler(MY_HANDLER)
