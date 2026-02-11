# GitHub Copilot Instructions for pysaunum

This repository contains `pysaunum`, a Python library for controlling Saunum sauna controllers via Modbus TCP. It is used by the [Saunum Home Assistant integration](https://www.home-assistant.io/integrations/saunum).

## Project Overview

- **Purpose**: Async Python client for Saunum sauna controllers
- **Protocol**: Modbus TCP (via pymodbus library)
- **Python**: 3.12+
- **Structure**: src layout (`src/pysaunum/`)

## Code Standards

### Python Requirements

- **Compatibility**: Python 3.12+
- **Type hints**: Required for all functions, methods, and variables (strict mypy)
- **Async/await**: All I/O operations must be async
- **Docstrings**: Required for all public classes and methods

### Code Style

- **Formatter**: Ruff (line length 88)
- **Linter**: Ruff + mypy (strict mode)
- **Language**: American English for all code, comments, and documentation

### Type Hints

```python
# ✅ Good - comprehensive type hints
async def async_set_target_temperature(self, temperature: int) -> None:
    """Set the target temperature."""

# ✅ Good - Optional fields use | None
current_temperature: float | None
```

### Docstrings

```python
# ✅ Good - concise module header
"""Python library for controlling Saunum sauna controllers."""

# ✅ Good - method docstring with raises
async def connect(self) -> None:
    """Connect to the sauna controller.

    Raises:
        SaunumConnectionError: If connection fails.
    """
```

## Architecture

### File Structure

```
src/pysaunum/
├── __init__.py      # Public API exports
├── client.py        # SaunumClient - main async client
├── const.py         # Constants (ports, limits, register addresses)
├── exceptions.py    # Exception hierarchy
├── models.py        # SaunumData dataclass
└── py.typed         # PEP-561 marker
```

### Exception Hierarchy

All exceptions inherit from `SaunumException`:

- `SaunumConnectionError` - Connection failures
- `SaunumCommunicationError` - Communication errors
- `SaunumTimeoutError` - Request timeouts
- `SaunumInvalidDataError` - Invalid data received

### Client Patterns

```python
# ✅ Preferred - factory method with auto-connect
client = await SaunumClient.create("192.168.1.100")

# ✅ Preferred - context manager
async with SaunumClient.create("192.168.1.100") as client:
    data = await client.async_get_data()

# Also supported - manual connect
client = SaunumClient(host="192.168.1.100")
await client.connect()
```

### Data Model

`SaunumData` is a dataclass with optional fields for sauna state:

- Session control: `session_active`, `target_temperature`, `fan_speed`, etc.
- Sensors: `current_temperature`, `heater_elements_active`, `door_open`
- Alarms: `alarm_door_open`, `alarm_thermal_cutoff`, etc.

## Development Commands

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pysaunum --cov-report=term-missing

# Run specific test file
pytest tests/test_client.py -v
```

### Linting

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Ruff linting
ruff check src/pysaunum

# Ruff formatting
ruff format src/pysaunum

# Type checking
mypy src/pysaunum --strict
```

## Best Practices

### ✅ Do

- Use async/await for all Modbus operations
- Wrap pymodbus exceptions in pysaunum exceptions
- Use constants from `const.py` for register addresses and limits
- Add type hints to all function signatures
- Write pytest tests for new functionality
- Use `pytest-asyncio` for async test functions

### ❌ Don't

- Block the event loop with synchronous I/O
- Expose pymodbus types in the public API
- Use bare `except:` clauses
- Hardcode register addresses outside `const.py`
- Skip type annotations

### Error Handling Pattern

```python
# ✅ Good - wrap library exceptions
try:
    response = await self._client.read_holding_registers(address, count)
except ModbusException as err:
    raise SaunumCommunicationError(f"Failed to read registers: {err}") from err

# Process data outside try block
if response.isError():
    raise SaunumInvalidDataError("Invalid response from controller")
```

### Async Context Manager

```python
# ✅ Good - proper cleanup
async def __aenter__(self) -> Self:
    """Enter async context."""
    await self.connect()
    return self

async def __aexit__(self, *args: object) -> None:
    """Exit async context."""
    self.close()
```

## Testing Guidelines

- Use `pytest-asyncio` with `asyncio_mode = "auto"`
- Mock `pymodbus.client.AsyncModbusTcpClient` for unit tests
- Test both success and error paths
- Use fixtures for common test setup
- Timeout: 10 seconds per test

### Test Example

```python
@pytest.fixture
def mock_modbus_client():
    """Create a mock Modbus client."""
    with patch("pysaunum.client.AsyncModbusTcpClient") as mock:
        yield mock.return_value

async def test_get_data_success(mock_modbus_client):
    """Test successful data retrieval."""
    mock_modbus_client.read_holding_registers.return_value = MockResponse(...)

    client = SaunumClient(host="192.168.1.100")
    await client.connect()
    data = await client.async_get_data()

    assert data.session_active is False
```

## Constants Reference

Key constants from `const.py`:

| Constant                        | Value | Description                    |
| ------------------------------- | ----- | ------------------------------ |
| `DEFAULT_PORT`                  | 502   | Modbus TCP port                |
| `MIN_TEMPERATURE`               | 40    | Minimum target temp (°C)       |
| `MAX_TEMPERATURE`               | 100   | Maximum target temp (°C)       |
| `MIN_DURATION`                  | 0     | Minimum session duration (min) |
| `MAX_DURATION`                  | 720   | Maximum session duration (min) |
| `FAN_SPEED_OFF/LOW/MEDIUM/HIGH` | 0-3   | Fan speed levels               |
