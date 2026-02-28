# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-02-28

### Breaking Changes

- Removed `None` type from most `SaunumData` fields; boolean and integer fields now always have concrete values
  - `sauna_duration`, `fan_duration`, `target_temperature` are now `int` (0 = sauna type default)
  - `light_on`, `door_open`, `current_temperature`, `on_time`, `heater_elements_active` are no longer nullable
  - All alarm fields (`alarm_door_open`, `alarm_door_sensor`, etc.) are now `bool` instead of `bool | None`
- `sauna_type` field changed from `int | None` to `SaunaType | int` (enum for known types, raw int for unknown)
- `fan_speed` field changed from `int | None` to `FanSpeed | None` (returns enum member instead of raw int)
- Removed synchronous `close()` method; use `async_close()` instead
- `SaunumTimeoutError` now also inherits from `TimeoutError`
- `DEFAULT_TIMEOUT` changed from `int` (10) to `float` (10.0)

### Added

- `__repr__` method on `SaunumClient` for readable string representation
- `DEFAULT_DURATION`, `DEFAULT_FAN_DURATION`, and `DEFAULT_FAN_SPEED` to module exports
- Host validation in `SaunumClient.__init__`; raises `ValueError` for empty or blank hosts
- `SaunumTimeoutError` raised on connection timeout (previously only `SaunumConnectionError`)
- `NullHandler` added to package-level logger instead of client module logger

### Changed

- `_validate_registers` refactored from static method to module-level function
- Timeout parameter type changed from `int` to `float` across `__init__` and `create`
- `async_close()` simplified to call `self._client.close()` directly
- `__aenter__` return type changed from `SaunumClient` to `Self`
- `__aexit__` parameter type changed from `*args: Any` to `*args: object`
- All post-action log messages downgraded from `info` to `debug` level (session start/stop, temperature set, duration set, fan speed set, sauna type set, light control, connect, disconnect)
- Heater elements register comment updated to remove `(0-3)` constraint
- Ruff target version updated from `py311` to `py312` in `pyproject.toml`

### Removed

- Synchronous `close()` method with event loop detection logic
- `mock_register_responses` fixture from `tests/conftest.py`
- `asyncio`, `inspect`, and `threading` imports no longer needed in client

### Developer Experience

- CI coverage threshold raised from 95% to 100%
- Added `from __future__ import annotations` to all source modules
- Simplified and consolidated test suite

## [0.5.0] - 2026-02-11

### Breaking Changes

- Replaced `FAN_SPEED_OFF`, `FAN_SPEED_LOW`, `FAN_SPEED_MEDIUM`, `FAN_SPEED_HIGH` constants with `FanSpeed` IntEnum
- Replaced `SAUNA_TYPE_1`, `SAUNA_TYPE_2`, `SAUNA_TYPE_3` constants with `SaunaType` IntEnum
- `SaunumData` dataclass is now frozen (immutable)
- Removed deprecated constants from public API exports in `__init__.py`

### Added

- `FanSpeed` IntEnum (`OFF`, `LOW`, `MEDIUM`, `HIGH`) for type-safe fan speed control
- `SaunaType` IntEnum (`TYPE_1`, `TYPE_2`, `TYPE_3`) for type-safe sauna type selection
- `port` property to `SaunumClient` to expose the Modbus TCP port
- `device_id` property to `SaunumClient` to expose the Modbus device/unit ID

### Changed

- **Minimum Python version raised from 3.11 to 3.12**
- Fan speed validation now uses `in FanSpeed` enum membership instead of range checks
- Sauna type validation now uses `in SaunaType` enum membership instead of tuple comparison
- Fan duration validation now uses chained comparison (`MIN_FAN_DURATION <= minutes <= MAX_FAN_DURATION`)

### Improved

- Updated README examples to use `FanSpeed` and `SaunaType` enums
- Updated README to use `async_close()` instead of `close()` for connection cleanup
- Updated `example.py` to use new enum-based constants

### Developer Experience

- Extracted shared test fixtures into `tests/conftest.py`
- Consolidated factory method tests from `tests/test_improvements.py` into `tests/test_client.py`
- Removed `tests/test_improvements.py`

## [0.4.0] - 2026-02-08

### Added

- Debug and info logging for all client operations (connect, data fetch, write commands, close)
- `__all__` exports to `client.py`, `const.py`, `exceptions.py`, and `models.py` for explicit public API
- Dependabot configuration for automated pip and GitHub Actions dependency updates
- GitHub Copilot instructions (`.github/copilot-instructions.md`)
- Codespell pre-commit hook for spell checking
- Package build and twine check steps in CI workflow
- Codecov test results upload in CI
- Coverage threshold enforcement (`--cov-fail-under=95`) in CI

### Changed

- Disconnect log message changed from "Closed connection" to "Disconnected from" for clarity
- `is_connected` property now returns `bool` explicitly via `bool()` cast
- CI actions updated: `actions/checkout` v4 → v6, `actions/setup-python` v5 → v6, `codecov/codecov-action` v4 → v5
- Ruff and mypy now lint and type-check the entire project (including `tests/`) instead of only `src/`
- Pre-commit mypy hook includes `pytest` as additional dependency and runs on `tests/` directory
- Removed `poetry-check` pre-commit hook
- `pyproject.toml`: added `tool.setuptools` include-package-data, mypy overrides for tests, and codespell config

### Improved

- README.md updated with CI, coverage, PyPI, Python version, and license badges
- README.md updated with dynamic Home Assistant installation count and quality scale badges
- CONTRIBUTING.md expanded with pre-commit hook details table and additional usage instructions

## [0.3.0] - 2026-01-13

### Added

- `async_close()` method for proper async cleanup of connections
- Comprehensive register validation before parsing
- Timeout handling for write operations

### Changed

- Async context manager (`__aexit__`) now uses `async_close()` instead of `close()`
- Synchronous `close()` method enhanced to handle awaitable close methods

### Improved

- Better error messages for invalid register data
- Type safety with explicit casting to avoid pylint warnings
- More robust connection lifecycle management

### Fixed

- @mikz fixed issue negative current temperature decoding

### Developer Experience

- Additional test coverage for:
  - Write timeout scenarios
  - Async close with coroutine handling
  - Register validation edge cases

## [0.2.0] - 2025-11-01

### Added

- Factory method pattern (`SaunumClient.create()`) for explicit async initialization
  - Automatically establishes connection before returning client
  - Recommended for production use to guarantee connection state
  - Example: `client = await SaunumClient.create("192.168.1.100")`
- Pre-commit configuration with automated code quality checks
  - Ruff linter and formatter
  - MyPy strict type checking
  - Standard pre-commit hooks (trailing whitespace, EOF, YAML/JSON/TOML validation)
- Comprehensive tests for factory method (5 new tests)
- Advanced usage examples in `example_factory.py`
- NullHandler to logger to prevent "no handlers found" warnings

### Changed

- Version management now uses `importlib.metadata` for single source of truth from `pyproject.toml`
- Updated README.md to recommend factory method as primary usage pattern
- Updated CONTRIBUTING.md with pre-commit setup and workflow instructions
- Updated MANIFEST.in to include all documentation files

### Improved

- Debug logging added to factory method for better troubleshooting
- Documentation expanded with factory method examples and patterns
- Test coverage maintained at 100% (61 tests total, up from 56)

### Developer Experience

- Pre-commit hooks ensure code quality before commits
- Automated linting and formatting with ruff
- Strict type checking with mypy
- Single command setup: `pip install pre-commit && pre-commit install`

## [0.1.0] - 2025-10-26

### Added

- Initial release of pysaunum
- Async client for Saunum sauna controllers
- Support for all controller features:
  - Temperature control (40-100°C)
  - Session management
  - Fan speed control (0-3)
  - Light control
  - Heater monitoring
  - Alarm status monitoring
- Comprehensive error handling with specific exceptions
- Full type hints support (py.typed)
- Extensive test coverage (>95%)

### Dependencies

- pymodbus >= 3.11.2

[Unreleased]: https://github.com/mettolen/pysaunum/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/mettolen/pysaunum/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/mettolen/pysaunum/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/mettolen/pysaunum/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/mettolen/pysaunum/releases/tag/v0.3.0
[0.2.0]: https://github.com/mettolen/pysaunum/releases/tag/v0.2.0
[0.1.0]: https://github.com/mettolen/pysaunum/releases/tag/v0.1.0
