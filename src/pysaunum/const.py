"""Constants for Saunum sauna controllers."""

from typing import Final

# Default connection settings
DEFAULT_PORT: Final = 502
DEFAULT_DEVICE_ID: Final = 1
DEFAULT_TIMEOUT: Final = 10

# Modbus register addresses - Holding Registers (Read/Write)
REG_SESSION_ACTIVE: Final = 0
REG_TARGET_TEMPERATURE: Final = 4

# Modbus register addresses - Input Registers (Read-Only)
REG_CURRENT_TEMP: Final = 100
REG_HEATER_STATUS_OFFSET: Final = 3  # Offset from REG_CURRENT_TEMP

# Temperature ranges in Celsius (device native unit)
MIN_TEMPERATURE: Final = 40
MAX_TEMPERATURE: Final = 100
DEFAULT_TEMPERATURE: Final = 80

# Write settle delay (seconds) - time to wait after writing before reading
WRITE_SETTLE_SECONDS: Final = 1
