"""Smart defaults and user overrides for project metadata (GEN element).

Provides factory defaults from the bundled TOML, user overrides from config.json,
and runtime smart logic (username initials, date auto-fill, KDF filename stem).
"""

from __future__ import annotations

import os
import re
import tomllib
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any


def load_factory_defaults() -> dict[str, Any]:
    """Load factory defaults from the bundled project_defaults.toml.

    Returns:
        Nested dict with keys: company, project, engineering.
    """
    toml_bytes = files("pykorf.use_case").joinpath("project_defaults.toml").read_bytes()
    return tomllib.loads(toml_bytes.decode("utf-8"))


def build_smart_defaults(kdf_path: str | Path | None = None) -> dict[str, str]:
    """Build flat dict of smart default values for project info fields.

    Priority: user config.json overrides > runtime smart values > factory TOML defaults.

    Args:
        kdf_path: Active .kdf path, used to derive item_name2 from the filename stem.

    Returns:
        Flat dict with keys: company1, company2, project_name1, project_name2,
        item_name1, item_name2, prepared_by, checked_by, approved_by, date,
        project_no, revision.
    """
    from pykorf.use_case.preferences import get_project_info_overrides

    factory = load_factory_defaults()
    overrides = get_project_info_overrides()

    co = factory.get("company", {})
    pr = factory.get("project", {})
    en = factory.get("engineering", {})

    company1: str = overrides.get("company1", co.get("company1", ""))
    company2: str = overrides.get("company2", co.get("company2", ""))
    project_name1: str = overrides.get("project_name1", pr.get("name1", ""))
    project_name2: str = overrides.get("project_name2", pr.get("name2", ""))
    item_name1: str = overrides.get("item_name1", pr.get("item_name1", ""))
    checked_by: str = overrides.get("checked_by", en.get("checked_by", ""))
    approved_by: str = overrides.get("approved_by", en.get("approved_by", ""))
    project_no: str = overrides.get("project_no", en.get("project_no", ""))
    revision: str = overrides.get("revision", en.get("revision", "A"))

    item_name2: str = overrides.get("item_name2", "")
    if not item_name2:
        if pr.get("item_name2_from_filename", False) and kdf_path is not None:
            item_name2 = Path(kdf_path).stem
        else:
            item_name2 = pr.get("item_name2", "")

    prepared_by: str = overrides.get("prepared_by", "")
    if not prepared_by:
        if en.get("prepared_by_from_username", False):
            username = os.environ.get("USERNAME", os.environ.get("USER", ""))
            fmt = en.get("prepared_by_format", "initials")
            prepared_by = re.sub(r"[^A-Z]", "", username) if fmt == "initials" else username
        else:
            prepared_by = en.get("prepared_by", "")

    date: str = overrides.get("date", "")
    if not date:
        if en.get("date_auto", False):
            date = datetime.today().strftime(en.get("date_format", "%d/%m/%y"))
        else:
            date = en.get("date", "")

    return {
        "company1": company1,
        "company2": company2,
        "project_name1": project_name1,
        "project_name2": project_name2,
        "item_name1": item_name1,
        "item_name2": item_name2,
        "prepared_by": prepared_by,
        "checked_by": checked_by,
        "approved_by": approved_by,
        "date": date,
        "project_no": project_no,
        "revision": revision,
    }
