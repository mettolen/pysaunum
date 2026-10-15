"""Python library for controlling Saunum sauna controllers."""

from __future__ import annotations

import logging
from importlib.metadata import version

from .client import SaunumClient
from .const import (
    AUTOLEIL_BUTTON_TIMEOUTS,
    AUTOLEIL_DURATION_STEP,
    AUTOLEIL_HUMIDITY_TEMPERATURE_SUM,
    DEFAULT_DURATION,
    DEFAULT_FAN_DURATION,
    DEFAULT_FAN_SPEED,
    DEFAULT_PORT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    MAX_AUTOLEIL_DURATION,
    MAX_AUTOLEIL_INTERVAL,
    MAX_AUTOLEIL_WATER_AMOUNT,
    MAX_DURATION,
    MAX_FAN_DURATION,
    MAX_FAN_SPEED,
    MAX_TEMPERATURE,
    MIN_AUTOLEIL_DURATION,
    MIN_AUTOLEIL_INTERVAL,
    MIN_AUTOLEIL_WATER_AMOUNT,
    MIN_DURATION,
    MIN_FAN_DURATION,
    MIN_FAN_SPEED,
    MIN_TEMPERATURE,
    AutoLeilMode,
    ControllerState,
    FanSpeed,
    Notification,
    SaunaSessionState,
    SaunaType,
    StartBlockReason,
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

logging.getLogger(__name__).addHandler(logging.NullHandler())

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
    "AUTOLEIL_HUMIDITY_TEMPERATURE_SUM",
    "MIN_AUTOLEIL_INTERVAL",
    "MAX_AUTOLEIL_INTERVAL",
    "MIN_AUTOLEIL_WATER_AMOUNT",
    "MAX_AUTOLEIL_WATER_AMOUNT",
    "MIN_AUTOLEIL_DURATION",
    "MAX_AUTOLEIL_DURATION",
    "AUTOLEIL_DURATION_STEP",
    "AUTOLEIL_BUTTON_TIMEOUTS",
    "MIN_TEMPERATURE",
    "MAX_TEMPERATURE",
    "MIN_DURATION",
    "MAX_DURATION",
    "MIN_FAN_DURATION",
    "MAX_FAN_DURATION",
    "MIN_FAN_SPEED",
    "MAX_FAN_SPEED",
    "AutoLeilMode",
    "ControllerState",
    "FanSpeed",
    "Notification",
    "SaunaSessionState",
    "SaunaType",
    "StartBlockReason",
]
