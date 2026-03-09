# Changelog

All notable changes to pyKorf will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- TUI application for PMS and HMB workflows
- Bulk calculation utilities
- Enhanced visualization with network diagrams
- Line number management

### Changed

- Refactored model architecture with service layer pattern
- Improved connectivity and layout services

## [0.2.0] - 2025-03-09

### Added

- Enterprise API features
  - Type-safe Pydantic models (`pykorf.types`)
  - Configuration management system (`pykorf.config`)
  - Structured logging (`pykorf.log`)
  - Export functionality (`pykorf.export`)
  - Enhanced exceptions with context
- MkDocs documentation
- Use case processors for PMS and HMB workflows

### Changed

- Improved type hints throughout
- Enhanced error messages with suggestions
- Better validation with detailed issue reporting

## [0.1.0] - 2024-01-15

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
