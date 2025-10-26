# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- New features that have been added

### Changed

- Changes to existing functionality

### Deprecated

- Features that will be removed in upcoming releases

### Removed

- Features that have been removed

### Fixed

- Bug fixes

### Security

- Security improvements

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

[Unreleased]: https://github.com/mettolen/pysaunum/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mettolen/pysaunum/releases/tag/v0.1.0
