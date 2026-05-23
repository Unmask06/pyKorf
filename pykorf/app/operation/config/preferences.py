"""User preferences and state management for pyKorf — re-export facade.

Delegates to sub-modules:
- _core:   load_config / save_config / cache
- _paths:  file / folder path preferences
- _settings: license, trial, SharePoint, interaction, timestamps
"""

from __future__ import annotations

from pykorf.app.operation.config._core import clear_config_cache, load_config, save_config  # noqa: F401
from pykorf.app.operation.config._paths import (  # noqa: F401
    add_pinned_folder,
    add_recent_file,
    get_doc_register_excel_path,
    get_last_batch_folder_path,
    get_last_batch_path_keyword_filter,
    get_last_hmb_path,
    get_last_kdf_path,
    get_last_report_path,
    get_pinned_folders,
    get_pms_excel_path,
    get_recent_files,
    record_opened_file,
    remove_pinned_folder,
    set_doc_register_excel_path,
    set_last_batch_folder_path,
    set_last_batch_path_keyword_filter,
    set_last_hmb_path,
    set_last_kdf_path,
    set_last_report_path,
    set_pms_excel_path,
)
from pykorf.app.operation.config._settings import (  # noqa: F401
    get_doc_register_db_last_imported,
    get_doc_register_sp_site_url,
    get_global_parameters_selected,
    get_last_interaction,
    get_license_key,
    get_pms_excel_last_imported,
    get_project_info_overrides,
    get_skip_sp_override,
    get_sp_overrides,
    get_stream_excel_last_imported,
    get_trial_start,
    set_doc_register_db_last_imported,
    set_doc_register_sp_site_url,
    set_global_parameters_selected,
    set_last_interaction,
    set_license_key,
    set_pms_excel_last_imported,
    set_project_info_overrides,
    set_skip_sp_override,
    set_sp_overrides,
    set_stream_excel_last_imported,
    set_trial_start,
)
