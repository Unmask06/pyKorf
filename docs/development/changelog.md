# Changelog

All notable changes to pyKorf will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Enterprise API features
  - Type-safe Pydantic models (`pykorf.types`)
  - Configuration management system (`pykorf.config`)
  - Structured logging (`pykorf.log`)
  - Export functionality (`pykorf.export`)
  - Query DSL (`pykorf.query`)
  - Enhanced exceptions with context
- CLI interface with rich output
- MkDocs documentation

### Changed

- Improved type hints throughout
- Enhanced error messages with suggestions
- Better validation with detailed issue reporting

## [0.2.0] - 2024-01-XX

### Added

- Query DSL for filtering elements
- Export to JSON, YAML, Excel, CSV
- Configuration management
- Structured logging
- Type-safe data models

### Changed

- Refactored definitions into subpackage
- Improved element wrapper classes
- Better error handling with context

## [0.1.0] - 2024-01-XX

### Added

- Initial release
- Core Model class for loading/saving KDF files
- Element wrapper classes (Pipe, Pump, Valve, etc.)
- Parser for KDF format
- Multi-case support via CaseSet
- Results extraction
- Connectivity management
- Layout and positioning
- Validation
- Visualization with PyVis
- GUI automation (Windows)
