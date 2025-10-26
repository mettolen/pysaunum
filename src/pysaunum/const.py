"""Constants for Saunum sauna controllers."""

from typing import Final

# Default connection settings
DEFAULT_PORT: Final = 502
DEFAULT_DEVICE_ID: Final = 1
DEFAULT_TIMEOUT: Final = 10  # seconds

# Modbus register addresses - Holding Registers (Read/Write Control Parameters)
REG_SESSION_ACTIVE: Final = 0  # Session on/off control 0=Off, 1=On
REG_SAUNA_TYPE: Final = 1  # Sauna type setting (0-2)
REG_SAUNA_DURATION: Final = 2  # Session duration in minutes (0-720), 0=type defined
REG_FAN_DURATION: Final = 3  # Fan duration in minutes (0-30), 0=type defined
REG_TARGET_TEMPERATURE: Final = 4  # Temperature setpoint in °C (40-100), 0=type defined
REG_FAN_SPEED: Final = 5  # Fan speed setting (0-3), 0=Off, 1=Low, 2=Medium, 3=High
REG_LIGHT_CONTROL: Final = 6  # Light on/off control (0=Off, 1=On)

# Modbus register addresses - Status Sensors (Read-Only)
REG_CURRENT_TEMP: Final = 100  # Current temperature in °C
REG_ON_TIME_HIGH: Final = 101  # On time high 16-bits (seconds)
REG_ON_TIME_LOW: Final = 102  # On time low 16-bits (seconds)
REG_HEATER_STATUS: Final = 103  # Number of heater elements active (0-3)
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

MIN_DURATION: Final = 0  # Minimum session duration (minutes)
MAX_DURATION: Final = 720  # Maximum session duration (minutes)
DEFAULT_DURATION: Final = 120  # Default session duration (minutes)

MIN_FAN_DURATION: Final = 0  # Minimum fan duration (minutes)
MAX_FAN_DURATION: Final = 30  # Maximum fan duration (minutes)
DEFAULT_FAN_DURATION: Final = 10  # Default fan duration (minutes)

MIN_FAN_SPEED: Final = 0  # Minimum fan speed (Off)
MAX_FAN_SPEED: Final = 3  # Maximum fan speed (High)
DEFAULT_FAN_SPEED: Final = 2  # Default fan speed (Medium)

# Fan speed levels
FAN_SPEED_OFF: Final = 0  # Fan off
FAN_SPEED_LOW: Final = 1  # Low speed
FAN_SPEED_MEDIUM: Final = 2  # Medium speed
FAN_SPEED_HIGH: Final = 3  # High speed

# Sauna types
SAUNA_TYPE_1: Final = 0  # Sauna type 1
SAUNA_TYPE_2: Final = 1  # Sauna type 2
SAUNA_TYPE_3: Final = 2  # Sauna type 3

# Status values
STATUS_OFF: Final = 0
STATUS_ON: Final = 1
