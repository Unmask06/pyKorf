"""Configuration and data files management for pyKorf.

This module serves as a unified facade for path resolution,
user preferences, and legacy configurations.

Please prefer importing from the specific modules:
- pykorf.use_case.paths
- pykorf.use_case.preferences
- pykorf.use_case.pms
- pykorf.use_case.hmb
"""

from __future__ import annotations

# Re-export Stream functions
from pykorf.use_case.hmb import (
    get_stream_path,
    import_stream_from_excel,
    load_stream_data,
    save_stream_data,
)

# Re-export path definitions and functions
from pykorf.use_case.paths import (
    APP_NAME,
    CONFIG_FILENAME,
    DATA_SUBDIR,
    DEFAULT_CONFIG_DIR,
    LEGACY_CONFIG_DIR,
    MIGRATION_MARKER,
    PROJECT_ROOT,
    _get_platform_config_dir,
    _migrate_from_legacy,
    _needs_migration,
    ensure_config_dir,
    ensure_data_dir,
    get_config_dir,
    get_config_path,
    get_data_dir,
    list_config_files,
)

# Re-export PMS functions
from pykorf.use_case.pms import (
    get_pms_path,
    import_pms_from_excel,
    load_pms_data,
    save_pms_data,
)

# Re-export preference functions
from pykorf.use_case.preferences import (
    add_recent_file,
    get_global_settings_selected,
    get_last_batch_folder_path,
    get_last_excel_export_path,
    get_last_excel_import_path,
    get_last_hmb_path,
    get_last_interaction,
    get_last_kdf_path,
    get_pms_excel_path,
    get_recent_files,
    load_config,
    record_opened_file,
    save_config,
    set_global_settings_selected,
    set_last_batch_folder_path,
    set_last_excel_export_path,
    set_last_excel_import_path,
    set_last_hmb_path,
    set_last_interaction,
    set_last_kdf_path,
    set_pms_excel_path,
)

__all__ = [
    "APP_NAME",
    "CONFIG_FILENAME",
    "DATA_SUBDIR",
    "DEFAULT_CONFIG_DIR",
    "LEGACY_CONFIG_DIR",
    "MIGRATION_MARKER",
    "PROJECT_ROOT",
    "_get_platform_config_dir",
    "_migrate_from_legacy",
    "_needs_migration",
    "add_recent_file",
    "ensure_config_dir",
    "ensure_data_dir",
    "get_config_dir",
    "get_config_path",
    "get_data_dir",
    "get_global_settings_selected",
    "get_last_batch_folder_path",
    "get_last_excel_export_path",
    "get_last_excel_import_path",
    "get_last_hmb_path",
    "get_last_interaction",
    "get_last_kdf_path",
    "get_pms_excel_path",
    "get_pms_path",
    "get_recent_files",
    "get_stream_path",
    "import_pms_from_excel",
    "import_stream_from_excel",
    "list_config_files",
    "load_config",
    "load_pms_data",
    "load_stream_data",
    "record_opened_file",
    "save_config",
    "save_pms_data",
    "save_stream_data",
    "set_global_settings_selected",
    "set_last_batch_folder_path",
    "set_last_excel_export_path",
    "set_last_excel_import_path",
    "set_last_hmb_path",
    "set_last_interaction",
    "set_last_kdf_path",
    "set_pms_excel_path",
]
