# Changelog

All notable changes to pyKorf will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-03-23

### Added

- **Post-install cleanup in launcher**: After the first successful sync to AppData, `pykorf/`, `pyproject.toml`, and `VERSION` are automatically removed from the launch folder — only `pykorf.bat` is needed for all future runs

### Changed

- **Launcher UI redesign**: Installation steps now use a consistent panel-per-step layout (`┌─ [N/4] Title` / `│` / `└─`) with `✓` / `✗` status symbols, uniform indentation, and a subtitle bar setting user expectations; launch screen repeats the header for a clean transition into the app

---

## [0.3.0] - 2026-03-23

### Added

- **Clickable pipe list in Bulk Copy**: Pipe names in the right panel are now clickable buttons that fill the reference pipe input directly
- **HMB path persistence**: Last used HMB JSON file path is saved and restored across sessions (matching existing PMS path persistence)
- **Success notifications for PMS/HMB apply**: Banner notification shown after applying PMS or HMB data, consistent with report/import screens
- **Dynamic element list in Model Info**: Selecting any element type row (Feeds, Products, Pumps, Valves) updates the name list below the table in real time
- **Recent files list in File Picker**: Quick-select buttons for up to 10 recently opened KDF files with tooltips showing full paths
- **Real-time path validation in File Picker**: Live file size and modified date display as path is typed
- **Loading states on all async screens**: Spinner and disabled button during PMS, HMB, Global Settings, and Report generation operations
- **Main menu grouped sections**: Operations grouped into Model Operations, Analysis & Reports, and Configuration with section headers and icons

### Changed

- **Main menu**: "Global Settings" renamed to "Apply Global Settings" and moved to Model Operations section
- **Splash screen**: Improved layout with subtitle and tool description; fixed broken spinner (was printing frames inline instead of in-place)
- **Branch cleanup**: Consolidated to `main` and `dev` branches only; merged all feature work

### Fixed

- **Worker `finally` blocks not running**: Early validation `return` statements sat before `try` blocks in 5 workers — Apply button stayed permanently disabled on validation failure; all fixed
- **Per-keystroke disk writes in Generate Report**: Folder path was saved to disk on every keystroke; now saved once on generate
- **Debug print statements in SaveConfirmScreen**: Removed all `print()` debug calls from production save flow
- **Inline comments on element param constants**: Added parameter format comments to all 17 element classes

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