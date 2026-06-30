"""Tests for the 'What's New' module.

Covers:
- CHANGELOG parser (``_parse_version_section``)
- Public accessor (``get_whats_new``, ``mark_whats_new_seen``) with the
  ``_find_changelog_path`` patched to a temp file
- FastAPI routes (``/api/whats-new``, ``/api/whats-new/seen``)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pykorf.app.operation.config.preferences import (
    get_whats_new_last_seen_version,
    set_whats_new_last_seen_version,
)


# ── Sample CHANGELOG used by the parser tests ───────────────────────────────


SAMPLE_CHANGELOG = """\
# Changelog

All notable changes to pyKorf will be documented in this file.

## [2.0.0] - 2026-07-01

### What's New

- Big feature A
- Big feature B

### Improved

- Performance boost

## [1.0.0] - 2026-06-15

### What's New

- First stable release

### Fixed

- Bug 1
- Bug 2

## [0.9.0] - 2026-06-01

### What's New

- Initial beta
"""


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def temp_changelog():
    """Write SAMPLE_CHANGELOG to a temp file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_CHANGELOG)
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
def mock_config(tmp_path):
    from pykorf.app.operation.config._core import clear_config_cache

    clear_config_cache()
    config_file = tmp_path / "config.json"
    config_file.write_text("{}", encoding="utf-8")

    with patch("pykorf.app.operation.config._core.get_config_path", return_value=config_file):
        yield config_file


@pytest.fixture
def patched_changelog(temp_changelog):
    """Patch ``_find_changelog_path`` to return the temp file."""
    with patch(
        "pykorf.app.whats_new._find_changelog_path", return_value=temp_changelog
    ):
        yield temp_changelog


# ── Parser tests ────────────────────────────────────────────────────────────


class TestParseVersionSection:
    def test_parses_middle_version(self):
        from pykorf.app.whats_new import _parse_version_section

        result = _parse_version_section(SAMPLE_CHANGELOG, "1.0.0")
        assert result is not None
        assert result["version"] == "1.0.0"
        assert result["date"] == "2026-06-15"
        assert len(result["sections"]) == 2
        assert result["sections"][0]["title"] == "What's New"
        assert result["sections"][0]["items"] == ["First stable release"]
        assert result["sections"][1]["title"] == "Fixed"
        assert result["sections"][1]["items"] == ["Bug 1", "Bug 2"]

    def test_parses_latest_version(self):
        from pykorf.app.whats_new import _parse_version_section

        result = _parse_version_section(SAMPLE_CHANGELOG, "2.0.0")
        assert result is not None
        assert result["date"] == "2026-07-01"
        assert len(result["sections"]) == 2
        assert result["sections"][0]["title"] == "What's New"
        assert result["sections"][0]["items"] == ["Big feature A", "Big feature B"]
        assert result["sections"][1]["title"] == "Improved"

    def test_parses_last_version_at_eof(self):
        """Block runs to EOF when there is no following '## ' header."""
        from pykorf.app.whats_new import _parse_version_section

        result = _parse_version_section(SAMPLE_CHANGELOG, "0.9.0")
        assert result is not None
        assert result["date"] == "2026-06-01"
        assert len(result["sections"]) == 1
        assert result["sections"][0]["items"] == ["Initial beta"]

    def test_returns_none_for_unknown_version(self):
        from pykorf.app.whats_new import _parse_version_section

        result = _parse_version_section(SAMPLE_CHANGELOG, "99.99.99")
        assert result is None

    def test_handles_section_with_no_bullets(self):
        from pykorf.app.whats_new import _parse_version_section

        text = (
            "## [0.1.0] - 2026-05-01\n"
            "\n"
            "### What's New\n"
            "\n"
            "Some prose, no bullets.\n"
        )
        result = _parse_version_section(text, "0.1.0")
        assert result is not None
        assert result["sections"][0]["title"] == "What's New"
        assert result["sections"][0]["items"] == []

    def test_ignores_stray_content_outside_subsection(self):
        from pykorf.app.whats_new import _parse_version_section

        text = (
            "## [0.1.0] - 2026-05-01\n"
            "\n"
            "Some preamble text\n"
            "### What's New\n"
            "- item 1\n"
        )
        result = _parse_version_section(text, "0.1.0")
        assert result is not None
        assert len(result["sections"]) == 1
        assert result["sections"][0]["items"] == ["item 1"]


# ── Public API tests ────────────────────────────────────────────────────────


class TestGetWhatsNew:
    def test_unseen_when_no_last_seen(self, mock_config, patched_changelog):
        from pykorf.app.whats_new import get_whats_new
        import pykorf

        assert get_whats_new_last_seen_version() is None

        with patch.object(pykorf, "__version__", "1.0.0"):
            data = get_whats_new()

        assert data["version"] == "1.0.0"
        assert data["date"] == "2026-06-15"
        assert data["has_unseen"] is True
        assert len(data["sections"]) == 2

    def test_seen_when_last_seen_matches_current(self, mock_config, patched_changelog):
        from pykorf.app.whats_new import get_whats_new
        import pykorf

        set_whats_new_last_seen_version("1.0.0")

        with patch.object(pykorf, "__version__", "1.0.0"):
            data = get_whats_new()

        assert data["has_unseen"] is False

    def test_unseen_when_last_seen_is_older(self, mock_config, patched_changelog):
        from pykorf.app.whats_new import get_whats_new
        import pykorf

        set_whats_new_last_seen_version("0.9.0")

        with patch.object(pykorf, "__version__", "1.0.0"):
            data = get_whats_new()

        assert data["has_unseen"] is True

    def test_empty_when_no_changelog_entry_for_version(
        self, mock_config, patched_changelog
    ):
        from pykorf.app.whats_new import get_whats_new
        import pykorf

        with patch.object(pykorf, "__version__", "99.99.99"):
            data = get_whats_new()

        assert data["sections"] == []
        assert data["has_unseen"] is False
        assert data["date"] is None

    def test_empty_when_changelog_missing(self, mock_config):
        from pykorf.app.whats_new import get_whats_new

        with patch("pykorf.app.whats_new._find_changelog_path", return_value=None):
            data = get_whats_new()

        assert data["sections"] == []
        assert data["has_unseen"] is False

    def test_empty_for_dev_version(self, mock_config, patched_changelog):
        from pykorf.app.whats_new import get_whats_new
        import pykorf

        with patch.object(pykorf, "__version__", "dev"):
            data = get_whats_new()

        assert data["sections"] == []
        assert data["has_unseen"] is False


class TestMarkWhatsNewSeen:
    def test_records_current_version(self, mock_config):
        from pykorf.app.whats_new import mark_whats_new_seen
        import pykorf

        with patch.object(pykorf, "__version__", "1.2.3"):
            recorded = mark_whats_new_seen()

        assert recorded == "1.2.3"
        assert get_whats_new_last_seen_version() == "1.2.3"


# ── API route tests ─────────────────────────────────────────────────────────


class TestWhatsNewAPI:
    """Tests for the FastAPI whats-new routes."""

    @pytest.fixture
    def client(self, mock_config, patched_changelog):
        from fastapi.testclient import TestClient
        from pykorf.app.api.app import create_app

        app = create_app()
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    def test_get_returns_unseen_for_new_version(self, client):
        import pykorf

        with patch.object(pykorf, "__version__", "1.0.0"):
            resp = client.get("/api/whats-new")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.0.0"
        assert data["has_unseen"] is True
        assert len(data["sections"]) == 2

    def test_get_returns_seen_after_mark(self, client):
        import pykorf

        with patch.object(pykorf, "__version__", "1.0.0"):
            # first call — unseen
            first = client.get("/api/whats-new").json()
            assert first["has_unseen"] is True

            # mark as seen
            resp = client.post("/api/whats-new/seen", json={})
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"
            assert resp.json()["version"] == "1.0.0"

            # second call — seen
            second = client.get("/api/whats-new").json()
            assert second["has_unseen"] is False

    def test_get_empty_for_unknown_version(self, client):
        import pykorf

        with patch.object(pykorf, "__version__", "99.0.0"):
            resp = client.get("/api/whats-new")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sections"] == []
        assert data["has_unseen"] is False
        assert data["date"] is None
