"""Configuration and data files management for pyKorf.

This module serves as a unified facade for path resolution,
user preferences, and legacy configurations.

Please prefer importing from the specific modules:
- pykorf.app.paths
- pykorf.app.preferences
- pykorf.app.pms
- pykorf.app.hmb
"""

from __future__ import annotations

# Re-export Stream functions
from pykorf.app.operation.data_import.hmb import (
    get_stream_path,
    import_stream_from_excel,
    load_stream_data,
    save_stream_data,
)

# Re-export path definitions and functions
from pykorf.app.operation.config.paths import (
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
from pykorf.app.operation.data_import.pms import (
    get_pms_path,
    import_pms_from_excel,
    load_pms_data,
    save_pms_data,
)

# Re-export project info functions
from pykorf.app.operation.project.project_info import build_smart_defaults

# Re-export preference functions
from pykorf.app.operation.config.preferences import (
    get_project_info_overrides,
    set_project_info_overrides,
    add_recent_file,
    get_global_parameters_selected,
    get_license_key,
    get_sp_overrides,
    get_trial_start,
    set_license_key,
    set_sp_overrides,
    set_trial_start,
    get_last_batch_folder_path,
    get_last_report_path,
    get_last_hmb_path,
    get_last_interaction,
    get_last_kdf_path,
    get_pms_excel_last_imported,
    get_pms_excel_path,
    get_recent_files,
    get_stream_excel_last_imported,
    get_doc_register_excel_path,
    get_doc_register_sp_site_url,
    get_doc_register_db_last_imported,
    load_config,
    record_opened_file,
    save_config,
    set_global_parameters_selected,
    set_last_batch_folder_path,
    set_last_report_path,
    set_last_hmb_path,
    set_last_interaction,
    set_last_kdf_path,
    set_pms_excel_last_imported,
    set_pms_excel_path,
    set_stream_excel_last_imported,
    set_doc_register_excel_path,
    set_doc_register_sp_site_url,
    set_doc_register_db_last_imported,
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
    "build_smart_defaults",
    "ensure_config_dir",
    "ensure_data_dir",
    "get_config_dir",
    "get_config_path",
    "get_data_dir",
    "get_doc_register_db_last_imported",
    "get_doc_register_excel_path",
    "get_doc_register_sp_site_url",
    "get_global_parameters_selected",
    "get_last_batch_folder_path",
    "get_last_hmb_path",
    "get_last_interaction",
    "get_last_kdf_path",
    "get_last_report_path",
    "get_license_key",
    "get_pms_excel_last_imported",
    "get_pms_excel_path",
    "get_pms_path",
    "get_project_info_overrides",
    "get_recent_files",
    "get_sp_overrides",
    "get_stream_excel_last_imported",
    "get_stream_path",
    "get_trial_start",
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
    "set_doc_register_db_last_imported",
    "set_doc_register_excel_path",
    "set_doc_register_sp_site_url",
    "set_global_parameters_selected",
    "set_last_batch_folder_path",
    "set_last_hmb_path",
    "set_last_interaction",
    "set_last_kdf_path",
    "set_last_report_path",
    "set_license_key",
    "set_pms_excel_last_imported",
    "set_pms_excel_path",
    "set_project_info_overrides",
    "set_sp_overrides",
    "set_stream_excel_last_imported",
    "set_trial_start",
]
