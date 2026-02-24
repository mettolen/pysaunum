"""Python library for controlling Saunum sauna controllers."""

from importlib.metadata import version

from .client import SaunumClient
from .const import (
    DEFAULT_DURATION,
    DEFAULT_FAN_DURATION,
    DEFAULT_FAN_SPEED,
    DEFAULT_PORT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    MAX_DURATION,
    MAX_FAN_DURATION,
    MAX_FAN_SPEED,
    MAX_TEMPERATURE,
    MIN_DURATION,
    MIN_FAN_DURATION,
    MIN_FAN_SPEED,
    MIN_TEMPERATURE,
    FanSpeed,
    SaunaType,
)
from .exceptions import (
    SaunumCommunicationError,
    SaunumConnectionError,
    SaunumException,
    SaunumInvalidDataError,
    SaunumTimeoutError,
)
from .models import SaunumData

__version__ = version("pysaunum")

__all__ = [
    "SaunumClient",
    "SaunumData",
    "SaunumException",
    "SaunumConnectionError",
    "SaunumCommunicationError",
    "SaunumTimeoutError",
    "SaunumInvalidDataError",
    "DEFAULT_DURATION",
    "DEFAULT_FAN_DURATION",
    "DEFAULT_FAN_SPEED",
    "DEFAULT_PORT",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TIMEOUT",
    "MIN_TEMPERATURE",
    "MAX_TEMPERATURE",
    "MIN_DURATION",
    "MAX_DURATION",
    "MIN_FAN_DURATION",
    "MAX_FAN_DURATION",
    "MIN_FAN_SPEED",
    "MAX_FAN_SPEED",
    "FanSpeed",
    "SaunaType",
]
