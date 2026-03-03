"""Interactive Textual TUI for pyKorf use case operations.

A rich terminal UI for bulk operations on KDF files, built with Textual.

Module Structure:
    app: Main UseCaseTUI application class
    screens: Individual screen components
        - file_picker: File selection screen
        - main_menu: Central menu
        - bulk_copy: Bulk copy fluids screen
        - apply_pms: Apply PMS specs screen
        - apply_hmb: Apply HMB properties screen
        - model_info: Model information display
        - save_confirm: Save/discard confirmation dialog
"""

from __future__ import annotations

from pykorf.use_case.tui.app import UseCaseTUI, run_tui

__all__ = ["UseCaseTUI", "run_tui"]
