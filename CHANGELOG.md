# Changelog

All notable changes to pyKorf will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-03-16

### Added

- **Auto-update check**: Automatic GitHub release check on startup with Y/n prompt to install updates
- **CI quality summary**: Detailed results table showing pass/fail status for all checks (ruff, mypy, pytest)
- **Auto-issue on CI failure**: Issues created with `/oc` prefix to trigger OpenCode agent for automatic fix planning

### Changed

- **Single source of truth for version**: Version now defined only in `pyproject.toml`, eliminating hardcoded duplicates
- **CI workflow resilience**: All checks now run to completion even if earlier checks fail, providing complete analysis
- **Repository URLs**: Updated all GitHub links to `Unmask06/pykorf`

### Fixed

- **Issue-on-failure workflow**: Added `contents: read` permission for private repository checkout support

## [0.2.1] - 2026-03-15

### Added

- `summary()` method for Feed, Product, and Valve classes
- Enhanced Excel export functionality with single-sheet reports

### Changed

- Streamlined last interaction data handling in preferences and config menu
- Updated pyKorf launcher for enhanced installation
- Improved splash screen alignment in CLI

### Fixed

- Adjusted trial duration settings
- Removed PowerShell version-specific fixes

## [0.2.0] - 2026-03-14

### Added

- GitHub Actions workflow for Windows release builds
- Generate Report screen with dynamic element selection
- ResultExporter for calculated output extraction
- Pipe criteria validation and visualization
- Single-sheet Excel export with improved header formatting

### Changed

- Enhanced type hints across the codebase
- Removed deprecated `_get` and `_set` methods (use `get_param` and `set_param`)
- Refined dummy pipe settings in UI
- Enhanced file picker and global navigation

### Fixed

- Ruff lint errors in layout.py

## [0.1.2] - 2026-03-10

### Added

- Initial public release
- Core KDF file parsing and serialization
- Model API for reading, editing, and writing KORF hydraulic models
- TUI application for use case workflows
- PyVis network visualization
- Excel, JSON, YAML export capabilities