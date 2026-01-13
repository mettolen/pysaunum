# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[Unreleased]: https://github.com/mettolen/pysaunum/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/mettolen/pysaunum/releases/tag/v0.3.0
[0.2.0]: https://github.com/mettolen/pysaunum/releases/tag/v0.2.0
[0.1.0]: https://github.com/mettolen/pysaunum/releases/tag/v0.1.0
