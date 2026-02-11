# pysaunum

[![CI](https://github.com/mettolen/pysaunum/actions/workflows/ci.yml/badge.svg)](https://github.com/mettolen/pysaunum/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/mettolen/pysaunum/branch/main/graph/badge.svg)](https://codecov.io/gh/mettolen/pysaunum)
[![PyPI version](https://badge.fury.io/py/pysaunum.svg)](https://badge.fury.io/py/pysaunum)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pysaunum.svg)](https://pypi.org/project/pysaunum/)
[![Python versions](https://img.shields.io/pypi/pyversions/pysaunum.svg)](https://pypi.org/project/pysaunum/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python library for controlling [Saunum](https://saunum.com/) sauna controllers via Modbus TCP.

---

This library is used by the [Saunum](https://www.home-assistant.io/integrations/saunum) Home Assistant integration.

<a href="https://www.home-assistant.io/integrations/saunum/" target="_blank"><img alt="Dynamic Regex Badge" src="https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fwww.home-assistant.io%2Fintegrations%2Fsaunum%2F&search=(%5B%5Cd%2C%5D%2B)%5Cs*%3C%2Fa%3E%5Cs*active%20installations&replace=%241&style=for-the-badge&logo=homeassistant&label=Active%20installations&labelColor=%23f2f4f9&color=%2346bdf4"></a> <a href="https://www.home-assistant.io/docs/quality_scale/" target="_blank"><img alt="Dynamic Regex Badge" src="https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fwww.home-assistant.io%2Fintegrations%2Fsaunum%2F&search=%3Ca%20href%3D'%5B%5E'%5D*quality_scale%5B%5E'%5D*'%3E(%5B%5E%3C%5D%2B%3F)%20quality%3C%2Fa%3E&replace=%241&style=for-the-badge&logo=homeassistant&label=Quality%20scale&labelColor=%23f2f4f9&color=%2346bdf4"></a> <a href="https://my.home-assistant.io/redirect/config_flow_start?domain=saunum" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/Saunum-i?style=for-the-badge&logo=homeassistant&label=Add%20integration&labelColor=%23f2f4f9&color=%2346bdf4"></a>

## Features

- 🔌 **Async/await support** using asyncio with comprehensive error handling
- 🏠 **Sauna type** configuration (Type 1, 2, or 3 with 0-indexed values)
- 🌡️ **Temperature control** with zero-value support (40-100°C range, 0 = type defined)
- ⏱️ **Session management** with configurable duration (0-720 minutes, default 120, 0 = type defined)
- ⏲️ **Fan duration** control (0-30 minutes, 0 = type defined)
- 💨 **Fan control** with discrete speeds (0=Off, 1=Low, 2=Medium, 3=High)
- 💡 **Light control** for sauna lighting
- 🔥 **Heater monitoring** with element count (0-3 active elements)
- 🚨 **Alarm status** monitoring (door, temperature, sensor alarms)
- 🛡️ **Type hints** for better IDE support and development experience
- 📊 **Comprehensive data model** with optional fields and proper null handling

## Installation

```bash
pip install pysaunum
```

## Quick Start

### Using Factory Method (Recommended)

The factory method automatically establishes a connection before returning the client:

```python
import asyncio
from pysaunum import SaunumClient, SaunumConnectionError

async def main():
    try:
        # Create and connect - client is ready to use immediately
        client = await SaunumClient.create("192.168.1.100")

        # Read current state
        data = await client.async_get_data()
        print(f"Current temperature: {data.current_temperature}°C")
        print(f"Target temperature: {data.target_temperature}°C")
        print(f"Session active: {data.session_active}")
        print(f"Heater elements active: {data.heater_elements_active}")

        # Start a sauna session with configuration
        await client.async_set_target_temperature(80)  # Set to 80°C
        await client.async_set_sauna_duration(120)     # 2 hours
        await client.async_set_fan_speed(2)            # Medium fan
        await client.async_start_session()

        # Stop the session when done
        await client.async_stop_session()

    except SaunumConnectionError as err:
        print(f"Connection error: {err}")
    finally:
        # Close connection
        await client.async_close()

asyncio.run(main())
```

### Traditional Method

You can also create and connect manually:

```python
import asyncio
from pysaunum import SaunumClient, SaunumConnectionError

async def main():
    # Create client - replace with your sauna controller's IP
    client = SaunumClient(host="192.168.1.100", port=502, device_id=1)

    try:
        # Must explicitly connect before using
        await client.connect()

        # Read current state
        data = await client.async_get_data()
        print(f"Current temperature: {data.current_temperature}°C")

    except SaunumConnectionError as err:
        print(f"Connection error: {err}")
    finally:
        # Close connection
        await client.async_close()

asyncio.run(main())
```

## Context Manager Usage (Recommended)

```python
import asyncio
from pysaunum import SaunumClient
from pysaunum.const import FanSpeed, SaunaType

async def main():
    try:
        # Using async context manager automatically handles connection cleanup
        async with SaunumClient(host="192.168.1.100") as client:
            # Configure sauna
            await client.async_set_sauna_type(SaunaType.TYPE_2)  # Type 2 sauna
            await client.async_set_target_temperature(85)
            await client.async_set_fan_speed(FanSpeed.HIGH)

            # Start session
            await client.async_start_session()

            # Read updated state
            data = await client.async_get_data()
            print(f"Session started: {data.session_active}")
            print(f"Heater elements: {data.heater_elements_active}/3")

    except Exception as err:
        print(f"Error: {err}")

asyncio.run(main())
```

## Available Constants

```python
from pysaunum.const import (
    # Fan speed enum (IntEnum)
    FanSpeed,           # FanSpeed.OFF=0, LOW=1, MEDIUM=2, HIGH=3

    # Sauna type enum (IntEnum, 0-indexed)
    SaunaType,          # SaunaType.TYPE_1=0, TYPE_2=1, TYPE_3=2

    # Limits
    MIN_TEMPERATURE,    # 40°C
    MAX_TEMPERATURE,    # 100°C
    MIN_DURATION,       # 0 minutes
    MAX_DURATION,       # 720 minutes (12 hours)
    DEFAULT_DURATION,   # 120 minutes (2 hours)
    MIN_FAN_DURATION,   # 0 minutes
    MAX_FAN_DURATION,   # 30 minutes
)

# Fan speed values are IntEnum members
assert FanSpeed.OFF == 0
assert FanSpeed.HIGH == 3
assert 2 in FanSpeed  # Membership testing

# Sauna type values are IntEnum members
assert SaunaType.TYPE_1 == 0
assert SaunaType.TYPE_3 == 2
```

## API Reference

### Main Client Methods

| Method                               | Description                 | Parameters                |
| ------------------------------------ | --------------------------- | ------------------------- |
| `async_get_data()`                   | Read all current sauna data | None                      |
| `async_start_session()`              | Start sauna session         | None                      |
| `async_stop_session()`               | Stop sauna session          | None                      |
| `async_set_target_temperature(temp)` | Set target temperature      | `temp: int` (0, 40-100°C) |
| `async_set_sauna_duration(minutes)`  | Set session duration        | `minutes: int` (0-720)    |
| `async_set_fan_speed(speed)`         | Set fan speed               | `speed: int` (0-3)        |
| `async_set_fan_duration(minutes)`    | Set fan duration            | `minutes: int` (0-30)     |
| `async_set_sauna_type(type)`         | Set sauna type              | `type: int` (0-2)         |
| `async_set_light_control(enabled)`   | Control sauna light         | `enabled: bool`           |

### Data Model (SaunumData)

```python
@dataclass(frozen=True)
class SaunumData:
    # Session control
    session_active: bool                   # Session status
    sauna_type: int | None                 # Sauna type (0-2)
    sauna_duration: int | None             # Duration in minutes
    fan_duration: int | None               # Fan duration in minutes
    target_temperature: int | None         # Target temp in °C
    fan_speed: int | None                  # Fan speed (0-3)
    light_on: bool | None                  # Light status

    # Status sensors
    current_temperature: float | None      # Current temp in °C
    on_time: int | None                    # Device uptime in seconds
    heater_elements_active: int | None     # Active heater elements (0-3)
    door_open: bool | None                 # Door status

    # Alarm status
    alarm_door_open: bool | None           # Door alarm during heating
    alarm_door_sensor: bool | None         # Door open too long
    alarm_thermal_cutoff: bool | None      # Thermal protection
    alarm_internal_temp: bool | None       # Overheating alarm
    alarm_temp_sensor_short: bool | None   # Sensor short circuit
    alarm_temp_sensor_open: bool | None    # Sensor disconnected
```

### Exception Handling

```python
from pysaunum import (
    SaunumConnectionError,      # Connection issues
    SaunumCommunicationError,   # Modbus communication errors
    SaunumTimeoutError,         # Timeout errors
    SaunumInvalidDataError,     # Invalid data received
)

try:
    async with SaunumClient("192.168.1.100") as client:
        data = await client.async_get_data()
except SaunumConnectionError:
    print("Failed to connect to sauna controller")
except SaunumCommunicationError:
    print("Communication error with sauna controller")
except SaunumTimeoutError:
    print("Operation timed out")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/mettolen/pysaunum.git
cd pysaunum

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Testing & Quality

```bash
# Run all tests with coverage
pytest --cov=pysaunum --cov-report=term-missing

# Run type checking
mypy src/pysaunum

# Run linting and formatting
ruff check src/pysaunum
ruff format src/pysaunum

# Run pre-commit hooks (if installed)
pre-commit run --all-files
```

### Current Test Coverage

The library maintains **100% test coverage** with comprehensive tests including:

- ✅ Connection handling and error scenarios
- ✅ All API methods with valid and invalid inputs
- ✅ Modbus communication error handling
- ✅ Data parsing and validation
- ✅ Context manager functionality
- ✅ Exception hierarchy and error messages

## Requirements

- Python 3.11+
- Dependencies:
  - `pymodbus` >= 3.0.0 (Modbus TCP communication)
  - `asyncio` (built-in, async/await support)

## Compatibility

This library is tested and compatible with:

- Saunum sauna controllers with Modbus TCP interface
  - Tested with control panel v1.1.24 and power unit v1.1.43
- Home Assistant integration
- Python 3.11, 3.12, 3.13+

## Advanced Usage

### Monitoring Heater Elements

```python
data = await client.async_get_data()
print(f"Active heater elements: {data.heater_elements_active}/3")

# Heater elements show how many of the 3 elements are currently active
# 0 = No heating, 1-3 = Number of elements heating
```

### Alarm Monitoring

```python
data = await client.async_get_data()

# Check for any active alarms
alarms = [
    ("Door open during heating", data.alarm_door_open),
    ("Door sensor alarm", data.alarm_door_sensor),
    ("Thermal cutoff", data.alarm_thermal_cutoff),
    ("Internal overheating", data.alarm_internal_temp),
    ("Temperature sensor short", data.alarm_temp_sensor_short),
    ("Temperature sensor open", data.alarm_temp_sensor_open),
]

active_alarms = [name for name, active in alarms if active]
if active_alarms:
    print(f"Active alarms: {', '.join(active_alarms)}")
```

## Troubleshooting

### Connection Issues

1. **Check IP address**: Ensure the sauna controller IP is correct
2. **Network connectivity**: Verify network connection to the controller
3. **Modbus port**: Default port is 502, ensure it's not blocked by firewall
4. **Device ID**: Default device ID is 1, check controller configuration

### Common Error Patterns

```python
# Handle specific error types
try:
    await client.connect()
except SaunumConnectionError as err:
    if "timeout" in str(err).lower():
        print("Connection timeout - controller may be offline")
    elif "refused" in str(err).lower():
        print("Connection refused - check IP and port")
    else:
        print(f"Connection error: {err}")
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Setting up your development environment
- Code style and testing requirements
- Submitting pull requests
- Reporting bugs and requesting features

For major changes, please open an issue first to discuss what you would like to change.

## Credits

This library is designed to work with [Saunum](https://saunum.com/) sauna controllers and is used by the [Home Assistant Saunum integration](https://www.home-assistant.io/integrations/saunum/).

**Key Features Developed:**

- Complete Modbus TCP implementation for Saunum controllers
- Comprehensive error handling and recovery
- Type-safe API with full asyncio support
- 100% test coverage with extensive validation
- Production-ready reliability and performance
