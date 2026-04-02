# Changelog

All notable changes to pyKorf will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.1] - 2026-04-02

### Fixed

- pyKorf now automatically repairs a broken virtual environment on startup instead of silently failing. If the repair succeeds, it relaunches immediately. If it cannot be repaired, a clear message is shown asking you to contact the developer.

---

## [0.8.0] - 2026-04-02

### What's New

- License key support added — enter a key in Preferences to unlock pyKorf beyond the trial period without needing a new release.
- The trial period now starts from the first time you launch pyKorf, giving each installation a full 30-day window regardless of when the software was built.

### Improved

- Updates are now atomic: pyKorf backs up the current installation before applying a new version and automatically restores it if anything goes wrong mid-update.
- Updates skip rebuilding the virtual environment when no package dependencies have changed, cutting update time from ~30 seconds to ~2 seconds for most releases.
- Downloaded update packages are now verified against a SHA256 checksum before installation, protecting against corrupted or tampered downloads.
- Updates now install the correct distribution package instead of the raw source archive.

### Fixed

- Update no longer fails with "A directory already exists at: .venv" when the old virtual environment could not be fully removed.

---

## [0.7.1] - 2026-04-02

### Fixed

- Improved the release process to prevent the dev branch from diverging ahead of main during releases.

---

## [0.7.0] - 2026-04-01

### What's New

- Pipe sizing validation now checks the ρV² (momentum) criterion for gas and two-phase services, catching high-velocity impingement issues that dP and velocity limits alone would miss.
- If a sizing criterion value is zero (not configured), that check is now skipped entirely rather than falsely flagging every pipe.

### Improved

- Criteria lookups are now cached, making repeated validation runs on large models noticeably faster.
- The "Criteria Check" column in Excel exports now shows **PASS** or **FAIL** instead of a raw true/false value, making reports easier to read at a glance.

---

## [0.6.4] - 2026-04-01

### Fixed

- The References page now saves correctly when editing remarks or hold items.
- All model operations (Apply PMS, Apply HMB, Bulk Copy, Global Parameters, Pipe Criteria) now save the model before and after the operation to prevent data loss.

---

## [0.6.3] - 2026-04-01

### What's New

- Pipe layout tools now support page size configuration, boundary definitions, and grid alignment for precise diagram positioning.

---

## [0.6.2] - 2026-04-01

### What's New

- Pipe layout now has automated routing tools — pipes can be arranged using orthogonal routing, polyline paths, flow-based positioning, and alignment helpers directly from the model API.
- Pipe sizing criteria has been overhauled with a more comprehensive lookup system covering liquid, gas, and two-phase services.

### Improved

- Automatic updates now install silently without a confirmation prompt — the application informs you and installs immediately.

### Fixed

- **Rename Line from NOTES** now correctly appends `_1`, `_2` suffixes when multiple pipes share the same extracted line number, instead of silently skipping the duplicate rename.

---

## [0.6.1] - 2026-03-30

### What's New

- A new **Pump Shut-Off Margin** global parameter sets the raise shut-off margin factor on all pumps in one click.

### Improved

- All operations (Apply PMS, Apply HMB, Bulk Copy Fluids, Global Parameters) now save the model automatically — no separate Save step needed.
- The **Save** button has been removed from the navbar since saving is now handled by each operation.
- Global parameter setting descriptions use plain language instead of raw KDF parameter codes.
- The KDF filename badge in the navbar now uses a clean, minimal style that blends with the UI.

## [0.6.0] - 2026-03-30

### What's New

- The References page now has **Remarks** and **Hold Items** text areas alongside Design Basis — all three are saved with the model and included in the first sheet of the generated report.
- The Excel report first sheet now includes Remarks and Hold Items sections, prints in **landscape**, and uses consistent column widths across all text sections.
- Pipe criteria now **pre-fills State and Criteria from the KDF file** — if a pipe already has a sizing code set in the model (`SIZ` parameter), the table populates automatically on load without needing to run Auto-predict.
- The Pipe Criteria table has **multi-select checkboxes** — tick individual pipes or use the header checkbox to select all visible rows, then apply a State and Criteria to all selected pipes at once.
- Calculated dP and velocity values in the Pipe Criteria table are now **highlighted in red** when they breach the assigned criteria limits.
- The **Auto-predict button is automatically disabled** once every pipe has a State and Criteria assigned, preventing unnecessary re-runs.
- SharePoint path overrides can now be **edited inline** on the Preferences page — clicking the pencil icon opens an edit form in place without requiring a popup.

### Improved

- Pipe criteria dP and velocity values now display with **two decimal places** for better precision.
- Right-side content (Feeds, Products, Junctions, Misc Equipment) in the Excel report starts at column M, bringing it closer to the main pipe data.
- Report and Export file paths on the Reports page are now **read-only and always derived from the open KDF file** — no more stale paths carried over from previous sessions.
- All path fields on the Reports page are now single-line inputs for a cleaner layout.

### Fixed

- The Preferences page edit button now works correctly — the previous modal-based approach failed silently due to a Bootstrap JS issue; editing now happens inline on the same page.

---

## [0.5.2] - 2026-03-30

### Fixed

- Updating to a new version no longer leaves the application broken with missing packages (e.g. `pandas`) — dependencies are now re-installed from the package list on every update, not synced from a lockfile that may be out of date.

---

## [0.5.1] - 2026-03-30

### Fixed

- First-time installation no longer fails with "does not appear to be a Python project" — the distribution package now correctly includes `pyproject.toml`.
- The installer terminal no longer displays internal download source URLs during setup or updates.

---

## [0.5.0] - 2026-03-30

### What's New

- pyKorf is now a **web application** — the terminal interface has been replaced by a browser-based UI running locally at `http://localhost:8000`. No change to how you launch it; the browser opens automatically.
- A new **Pipe Sizing Criteria** page lets you assign a sizing code to every pipe in the model (pump suction, pump discharge, general gas line, two-phase, etc.). Criteria values are looked up automatically from the engineering tables.
- The criteria table now includes a **ρV² (momentum flux)** column so gas and two-phase lines can be checked against all three limits — pressure drop, velocity, and momentum — in one view.
- The criteria table also shows the **calculated values** from the model (actual dP/100 m, velocity, and ρV²) alongside the limits so you can see pass/fail without opening a separate report.
- A **References** page lets you store SharePoint links, design-basis documents, and data-source references alongside each model file.
- **Bulk Copy** lets you copy fluid properties from one reference pipe to many others in a single action — useful when a common process stream feeds multiple lines.
- A **reload button** (↻) in the header bar re-reads the KDF file from disk instantly, so changes made in the KORF GUI are reflected without restarting pyKorf.
- The KDF filename in the header now shows the file's last-modified time, confirming when the model on disk was last saved.
- SharePoint folder path overrides can be configured in Preferences so pyKorf resolves OneDrive-synced local paths to their SharePoint URLs for link sharing with the team.

### Improved

- The main menu groups actions into logical sections — Model Operations, Analysis & Reports, and Configuration — making it easier to find the right tool.
- The file picker shows recent files as quick-select buttons and displays the file size and modification date as you type a path.
- Pipe sizing criteria lookup tables for liquid, gas, and two-phase lines are shipped with the application as editable TOML files.
- Global Parameters (formerly Global Settings) has been reorganised so the available presets are clearer and easier to apply selectively.
- All browser pages are served with no-cache headers so the UI always reflects the latest model state after a reload or save.

### Fixed

- Navigating back in the browser no longer shows a stale cached page — every visit fetches fresh data from the server.
- The sizing criteria distribution package now correctly includes the TOML lookup tables (previously only JSON files were bundled, causing a startup error on fresh installs).

---

## [0.4.1] - 2026-03-25

### Fixed

- The in-app auto-update no longer fails with "No module named pip" — it now uses the bundled `uv` tool to reinstall, which works correctly with the lightweight virtual environment created by the installer.

---

## [0.4.0] - 2026-03-25

### What's New

- The launcher can now update itself automatically when a new version is available — set `AUTO_UPDATE=TRUE` and it will download and swap in the latest launcher without any manual steps.
- The launcher now enforces a major-version lock, so a single `.bat` bootstrapper handles download, install, and future upgrades end-to-end.

### Improved

- The launcher now waits longer (10 seconds instead of 5) before giving up on the version check, reducing false "no update" results on slower or proxied connections.
- If a self-update fails because the launcher file is in use, you now see a clear error message instead of silently relaunching the old version.
- The distribution package now correctly cleans up leftover source files on a version-matched reinstall and always includes the reports JSON.

---

## [0.3.4] - 2026-03-24

### Improved

- The file picker now shows the selected filename in green between the drag-and-drop hint and the path input, so you can confirm at a glance which file is loaded before clicking Load.

---

## [0.3.3] - 2026-03-24

### What's New

- When an update is available, pyKorf now shows a plain-English summary of what changed before asking you to install it — no more raw developer notes.
- Batch reports now show per-file progress (`[1/5] filename.kdf`) as each file is processed, so you always know where things stand.
- A `/release` workflow is available for maintainers to version, document, and publish releases in one step.

### Improved

- The auto-update installer now works correctly with the bat-based distribution — it downloads the latest release directly from GitHub, unpacks it into the correct location, and reinstalls in place.
- The update prompt shows a live spinner while the download and install runs, with a clear "restart required" message on success.

---

## [0.3.2] - 2026-03-24

### Added

- **EQN propagation on pipe rename**: Renaming a pipe in Global Settings now updates all EQN references across the model; implemented via `propagate_pipe_rename()` in `pykorf/elements/pipe.py`
- **Suction & Discharge Pressure in compressor summary**: `compressor.summary()` now includes `Suction Pressure` and `Discharge Pressure` fields
- **Description in element summaries**: `Feed`, `Product`, and `Compressor` summaries now include the `NAME` param description (index 1) appended to the element name
- **Misc Equipment summary with Pressure Drop**: `MiscEquipment.summary()` added; registered on the right panel in `ResultExporter`
- **Excel report metadata rows**: Report now opens with model title (from SYMBOL FSIZ=2), source filename, and case names before the tables
- **Excel report footer**: Auto-generated notice row appended after all tables reminding users not to edit directly
- **Structured key-checkpoint logging**: All major operations (`Load Model`, `Reload Model`, `Save Model`, `Validate`, `Load PMS`, `Load HMB`, `Process`, `Batch Report`, `Generate Report`) now emit `──` checkpoint logs to the `.log` file with consistent named loggers (`ModelCore`, `IOService`, `SummaryService`, `BatchProcessor`, `ResultExporter`, `GenerateReport`)

### Changed

- **Excel report header row height**: Header rows now use height 30 with `wrap_text=True` and `vertical="center"` alignment
- **AGENTS.md synced with CLAUDE.md**: Shell section corrected to Git Bash (Unix syntax, `&&` chaining); Architecture section expanded with Model Services table, TUI screen flow, and test patterns
- **`UnitConverter` per-instance in `ResultExporter`**: Replaced shared global singleton with a per-instance `UnitConverter()` to ensure correct unit handling

### Fixed

- **Report generation not captured in log file**: `ResultExporter` and `GenerateReport` screen lacked file-logger hooks; both now use named loggers that route to the active `.log` file

---

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