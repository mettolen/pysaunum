"""Python library for controlling Saunum sauna controllers."""

from importlib.metadata import version

from .client import SaunumClient
from .const import (
    DEFAULT_PORT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    FAN_SPEED_HIGH,
    FAN_SPEED_LOW,
    FAN_SPEED_MEDIUM,
    FAN_SPEED_OFF,
    MAX_DURATION,
    MAX_FAN_DURATION,
    MAX_FAN_SPEED,
    MAX_TEMPERATURE,
    MIN_DURATION,
    MIN_FAN_DURATION,
    MIN_FAN_SPEED,
    MIN_TEMPERATURE,
    SAUNA_TYPE_1,
    SAUNA_TYPE_2,
    SAUNA_TYPE_3,
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
    "FAN_SPEED_OFF",
    "FAN_SPEED_LOW",
    "FAN_SPEED_MEDIUM",
    "FAN_SPEED_HIGH",
    "SAUNA_TYPE_1",
    "SAUNA_TYPE_2",
    "SAUNA_TYPE_3",
]
