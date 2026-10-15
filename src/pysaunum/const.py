"""Constants for Saunum sauna controllers."""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Final

__all__ = [
    "DEFAULT_PORT",
    "DEFAULT_DEVICE_ID",
    "DEFAULT_TIMEOUT",
    "MIN_TEMPERATURE",
    "MAX_TEMPERATURE",
    "DEFAULT_TEMPERATURE",
    "MIN_DURATION",
    "MAX_DURATION",
    "DEFAULT_DURATION",
    "MIN_FAN_DURATION",
    "MAX_FAN_DURATION",
    "DEFAULT_FAN_DURATION",
    "MIN_FAN_SPEED",
    "MAX_FAN_SPEED",
    "DEFAULT_FAN_SPEED",
    "AUTOLEIL_HUMIDITY_TEMPERATURE_SUM",
    "MIN_AUTOLEIL_INTERVAL",
    "MAX_AUTOLEIL_INTERVAL",
    "MIN_AUTOLEIL_WATER_AMOUNT",
    "MAX_AUTOLEIL_WATER_AMOUNT",
    "MIN_AUTOLEIL_DURATION",
    "MAX_AUTOLEIL_DURATION",
    "AUTOLEIL_DURATION_STEP",
    "AUTOLEIL_BUTTON_TIMEOUTS",
    "AutoLeilMode",
    "FanSpeed",
    "SaunaSessionState",
    "SaunaType",
]

# Default connection settings
DEFAULT_PORT: Final = 502
DEFAULT_DEVICE_ID: Final = 1
DEFAULT_TIMEOUT: Final = 10.0  # seconds

# Modbus register addresses - Holding Registers (Read/Write Control Parameters)
REG_SESSION_ACTIVE: Final = 0  # Session on/off control 0=Off, 1=On
REG_SAUNA_TYPE: Final = 1  # Sauna preset index (0 to device-dependent N-1)
REG_SAUNA_DURATION: Final = 2  # Session duration (60-1080 min), 0=type default
REG_FAN_DURATION: Final = 3  # Fan duration in minutes (0-20), 0=type default
REG_TARGET_TEMPERATURE: Final = 4  # Temperature setpoint in °C (40-100), 0=type defined
REG_FAN_SPEED: Final = 5  # Fan speed setting (0-3), 0=Off, 1=Low, 2=Medium, 3=High
REG_LIGHT_CONTROL: Final = 6  # Light on/off control (0=Off, 1=On)
REG_SOFTWARE_RESTART: Final = 7  # Software restart command
REG_CLOSE_COOLDOWN: Final = 8  # Close active cooldown mode
REG_DISMISS_NOTIFICATIONS: Final = 9  # Dismiss on-screen notifications
REG_AUTOLEIL_MODE: Final = 10  # Humidity or interval mode
REG_AUTOLEIL_TARGET_HUMIDITY: Final = 11  # Target relative humidity
REG_AUTOLEIL_INTERVAL: Final = 12  # Automatic water throw interval
REG_AUTOLEIL_WATER_AMOUNT: Final = 13  # Water valve duration in 0.1 seconds
REG_AUTOLEIL_DURATION: Final = 14  # AutoLeil operating duration
REG_AUTOLEIL_READY_MODE: Final = 15  # Keep AutoLeil ready after its duration
REG_AUTOLEIL_AUTO_VENTILATION: Final = 16  # Automatic ventilation control
REG_AUTOLEIL_BUTTON_USE: Final = 17  # Physical AutoLeil button control
REG_AUTOLEIL_BUTTON_TIMEOUT: Final = 18  # Physical button timeout

SOFTWARE_RESTART_MAGIC: Final = 0xA55A

# Modbus register addresses - Status Sensors (Read-Only)
REG_CURRENT_TEMP: Final = 100  # Current temperature in °C
REG_ON_TIME_HIGH: Final = 101  # On time high 16-bits (seconds)
REG_ON_TIME_LOW: Final = 102  # On time low 16-bits (seconds)
REG_HEATER_STATUS: Final = 103  # Number of heater elements active
REG_DOOR_STATUS: Final = 104  # Door status (open/closed)

# Modbus register addresses - Alarm Status (Read-Only)
REG_ALARM_DOOR_OPEN: Final = 200  # Door open during heating alarm
REG_ALARM_DOOR_SENSOR: Final = 201  # Door open too long alarm
REG_ALARM_THERMAL_CUTOFF: Final = 202  # Thermal cutoff alarm
REG_ALARM_INTERNAL_TEMP: Final = 203  # Internal overheating alarm
REG_ALARM_TEMP_SENSOR_SHORT: Final = 204  # Temperature sensor shorted alarm
REG_ALARM_TEMP_SENSOR_OPEN: Final = 205  # Temperature sensor not connected alarm

# Register value ranges and defaults
MIN_TEMPERATURE: Final = 40
MAX_TEMPERATURE: Final = 100
DEFAULT_TEMPERATURE: Final = 80

MIN_DURATION: Final = 60  # Minimum non-default session duration (minutes)
MAX_DURATION: Final = 1080  # Maximum public sauna session duration (minutes)
DEFAULT_DURATION: Final = 120  # Default session duration (minutes)

MIN_FAN_DURATION: Final = 0  # Minimum fan duration (minutes)
MAX_FAN_DURATION: Final = 20  # Maximum fan duration (minutes)
DEFAULT_FAN_DURATION: Final = 10  # Default fan duration (minutes)

MIN_FAN_SPEED: Final = 0  # Minimum fan speed (Off)
MAX_FAN_SPEED: Final = 3  # Maximum fan speed (High)
DEFAULT_FAN_SPEED: Final = 2  # Default fan speed (Medium)

AUTOLEIL_HUMIDITY_TEMPERATURE_SUM: Final = 130
MIN_AUTOLEIL_INTERVAL: Final = 1  # minutes
MAX_AUTOLEIL_INTERVAL: Final = 25  # minutes
MIN_AUTOLEIL_WATER_AMOUNT: Final = 3  # 0.3 seconds
MAX_AUTOLEIL_WATER_AMOUNT: Final = 40  # 4.0 seconds
MIN_AUTOLEIL_DURATION: Final = 60  # minutes
MAX_AUTOLEIL_DURATION: Final = 1080  # minutes
AUTOLEIL_DURATION_STEP: Final = 30  # minutes
AUTOLEIL_BUTTON_TIMEOUTS: Final[tuple[int, ...]] = (
    5,
    15,
    30,
    60,
    120,
    180,
    240,
    300,
)


class AutoLeilMode(IntEnum):
    """AutoLeil operating modes."""

    HUMIDITY = 0
    INTERVAL = 1


# Fan speed levels
class FanSpeed(IntEnum):
    """Fan speed settings."""

    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# Sauna types
class SaunaType(IntEnum):
    """Convenience labels for the first three sauna preset indices."""

    TYPE_1 = 0
    TYPE_2 = 1
    TYPE_3 = 2


class SaunaSessionState(StrEnum):
    """Sauna session operating states."""

    INACTIVE = "inactive"
    HEATING = "heating"
    COOLDOWN = "cooldown"


# Status values
STATUS_OFF: Final = 0
STATUS_ON: Final = 1
