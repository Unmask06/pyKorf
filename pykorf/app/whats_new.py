"""'What's New' — parse the CHANGELOG and surface release notes to the UI.

The CHANGELOG.md is bundled alongside the package (see ``distribute.bat`` and
``[tool.setuptools.package-data]`` in ``pyproject.toml``). At runtime we locate
the file via a small candidate-path search so that both installed distributions
and source checkouts (dev mode) work transparently.

Only the section matching the current app version is returned — the modal is
intended to be a brief "here's what changed since you last saw this" notice,
not the full changelog history.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pykorf
from pykorf.app.operation.config.preferences import (
    get_whats_new_last_seen_version,
    set_whats_new_last_seen_version,
)


# ── Path resolution ─────────────────────────────────────────────────────────


def _find_changelog_path() -> Path | None:
    """Locate ``CHANGELOG.md`` in either the installed package or the source tree.

    Search order:
      1. ``<pykorf_package_dir>/CHANGELOG.md`` — installed wheel or built dist
         (where ``distribute.bat`` copies it to).
      2. ``<repo_root>/CHANGELOG.md`` — source checkout / dev mode, where
         ``pykorf/`` is a child of the repo root.

    Returns:
        Resolved path or ``None`` if the file cannot be located.
    """
    package_dir = Path(pykorf.__file__).resolve().parent
    candidates: list[Path] = [
        package_dir / "CHANGELOG.md",
        package_dir.parent / "CHANGELOG.md",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


# ── Parser ──────────────────────────────────────────────────────────────────


# A version section starts with "## [VERSION] - YYYY-MM-DD"
# Captures: 1 = version, 2 = date (may contain other chars but the date is the
# last "- <word>" token). Anchored to a full line so we don't false-match
# bullet points that mention a version.
_VERSION_HEADER = re.compile(r"^##\s+\[([^\]]+)\]\s+-\s+(.+?)\s*$")

# A subsection starts with "### <Title>" — must be a full line, not a bullet.
_SUBSECTION_HEADER = re.compile(r"^###\s+(.+?)\s*$")


def _parse_version_section(
    changelog_text: str, version: str
) -> dict[str, Any] | None:
    """Extract the release-notes block for a specific version from CHANGELOG.md.

    The block runs from the matching ``## [version]`` line up to the next
    ``## <other>`` line (or EOF). Within that block, ``### <Title>`` lines
    delimit sections and ``- item`` bullets are collected into the current
    section.

    Args:
        changelog_text: Full CHANGELOG.md contents.
        version: The version to look up (matched exactly inside ``[...]``).

    Returns:
        Dict with keys ``version``, ``date``, ``sections`` (list of
        ``{"title", "items"}`` dicts) or ``None`` if the version is not found.
    """
    lines = changelog_text.splitlines()
    start_idx: int | None = None
    date: str | None = None

    for idx, line in enumerate(lines):
        m = _VERSION_HEADER.match(line)
        if not m:
            continue
        if m.group(1).strip() == version:
            start_idx = idx + 1  # body starts after the header
            date = m.group(2).strip()
            break

    if start_idx is None:
        return None

    # Collect body until the next `## ` top-level header
    end_idx = len(lines)
    for idx in range(start_idx, len(lines)):
        if lines[idx].startswith("## ") and not lines[idx].startswith("### "):
            end_idx = idx
            break

    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in lines[start_idx:end_idx]:
        line = raw.rstrip()
        sub = _SUBSECTION_HEADER.match(line)
        if sub:
            current = {"title": sub.group(1).strip(), "items": []}
            sections.append(current)
            continue
        stripped = line.lstrip()
        if not current:
            # Stray content outside any `###` subsection (e.g. blank line, prose)
            continue
        if stripped.startswith("- "):
            current["items"].append(stripped[2:].strip())

    return {
        "version": version,
        "date": date,
        "sections": sections,
    }


# ── Public API ──────────────────────────────────────────────────────────────


def get_whats_new() -> dict[str, Any]:
    """Return the "What's New" content for the current version.

    The response is a plain dict (used by the FastAPI router to build a
    Pydantic response model). Shape::

        {
            "version": "0.47.0",
            "date": "2026-06-24",
            "sections": [{"title": "What's New", "items": ["..."]}, ...],
            "has_unseen": True,
        }

    ``has_unseen`` is ``True`` when the user has not yet acknowledged this
    version's notes. The frontend uses it to decide whether to auto-pop the
    modal on app start.

    Notes:
        - If the CHANGELOG.md is missing or has no entry for the current
          version (e.g. dev builds whose ``__version__`` is ``"dev"``), the
          response has empty sections and ``has_unseen=False`` — the modal is
          never shown.
        - ``__version__`` is read from the ``pykorf`` package at call time so
          a hot-reload of the dev server picks up version changes.
    """
    current_version = pykorf.__version__
    last_seen = get_whats_new_last_seen_version()

    changelog_path = _find_changelog_path()
    sections: list[dict[str, Any]] = []
    date: str | None = None
    if changelog_path is not None:
        try:
            text = changelog_path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        parsed = _parse_version_section(text, current_version)
        if parsed is not None:
            sections = parsed["sections"]
            date = parsed["date"]

    has_unseen = bool(sections) and (last_seen != current_version)

    return {
        "version": current_version,
        "date": date,
        "sections": sections,
        "has_unseen": has_unseen,
    }


def mark_whats_new_seen() -> str:
    """Record that the user has seen the "What's New" modal for the current version.

    Returns:
        The version string that was recorded (i.e. ``pykorf.__version__``).
    """
    version = pykorf.__version__
    set_whats_new_last_seen_version(version)
    return version
