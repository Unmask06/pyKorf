"""Reference documents manager for pyKorf web UI.

Stores design-basis notes and reference document links (SharePoint URLs or
local file paths) in a ``.pykorf`` sidecar file next to the KDF file.  The
sidecar is JSON and may grow to hold other per-model metadata in the future.

For each reference a Windows Internet Shortcut (``.url``) is created in a
``reference/`` sub-folder next to the KDF file.  ``.url`` files are plain
text — no extra dependencies required — and open in the default browser on
Windows, making them ideal for SharePoint links.

Storage layout::

    project/
      model.kdf
      model.pykorf            ← basis text + reference list (JSON)
      reference/
        P&ID-001.url          ← Internet Shortcut → SharePoint link
        Datasheet-HX-01.url
        ...
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ── Data model ────────────────────────────────────────────────────────────────

CATEGORIES: list[str] = [
    "P&ID",
    "PFD",
    "Datasheet",
    "Specification",
    "Calculation",
    "Drawing",
    "Report",
    "Standard",
    "Other",
]


@dataclass
class Reference:
    """A single reference document entry.

    Attributes:
        id: Unique identifier (UUID hex).
        name: Display name shown in the table and used as the shortcut filename.
        link: SharePoint URL or local file path.
        description: Free-text description / why this doc is relevant.
        category: One of :data:`CATEGORIES`.
    """

    id: str
    name: str
    link: str
    description: str = ""
    category: str = "Other"

    @classmethod
    def new(cls, name: str, link: str, description: str = "", category: str = "Other") -> Reference:
        """Create a new Reference with a generated UUID.

        Args:
            name: Display name.
            link: URL or file path.
            description: Optional description.
            category: Document category.

        Returns:
            A fresh Reference instance.
        """
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            link=link,
            description=description,
            category=category,
        )


@dataclass
class ReferencesStore:
    """Container for the design basis text and all reference entries.

    Attributes:
        basis: Free-text design basis / project notes.
        references: Ordered list of Reference entries.
    """

    basis: str = ""
    references: list[Reference] = field(default_factory=list)

    # ── Persistence ────────────────────────────────────────────────────────

    @classmethod
    def _sidecar_path(cls, kdf_path: Path) -> Path:
        """Return the ``.pykorf`` sidecar path for *kdf_path*.

        Args:
            kdf_path: Path to the .kdf file.

        Returns:
            Path of the form ``{stem}.pykorf`` beside the KDF.
        """
        return kdf_path.parent / f"{kdf_path.stem}.pykorf"

    @classmethod
    def _legacy_sidecar_path(cls, kdf_path: Path) -> Path:
        """Return the old ``.references.json`` sidecar path (migration only).

        Args:
            kdf_path: Path to the .kdf file.

        Returns:
            Path of the form ``{stem}.references.json`` beside the KDF.
        """
        return kdf_path.parent / f"{kdf_path.stem}.references.json"

    @classmethod
    def load(cls, kdf_path: Path) -> ReferencesStore:
        """Load from the ``.pykorf`` sidecar, or return an empty store.

        If no ``.pykorf`` file exists but the legacy ``.references.json`` file
        is present, it is loaded and immediately migrated to the new format.

        Args:
            kdf_path: Path to the .kdf file.

        Returns:
            Populated ReferencesStore.
        """
        sidecar = cls._sidecar_path(kdf_path)

        # Migrate from old .references.json if needed
        if not sidecar.is_file():
            legacy = cls._legacy_sidecar_path(kdf_path)
            if legacy.is_file():
                store = cls._parse_json(legacy)
                store.save(kdf_path)  # write new .pykorf
                return store
            return cls()

        return cls._parse_json(sidecar)

    @classmethod
    def _parse_json(cls, path: Path) -> ReferencesStore:
        """Parse a JSON sidecar file into a ReferencesStore.

        Args:
            path: JSON file to read.

        Returns:
            Populated ReferencesStore, or empty store on parse error.
        """
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            refs = [Reference(**r) for r in data.get("references", [])]
            return cls(basis=data.get("basis", ""), references=refs)
        except (json.JSONDecodeError, TypeError, KeyError):
            return cls()

    def save(self, kdf_path: Path) -> None:
        """Persist to the ``.pykorf`` sidecar beside the KDF file.

        Args:
            kdf_path: Path to the .kdf file; sidecar is written next to it.
        """
        sidecar = self._sidecar_path(kdf_path)
        payload = {
            "basis": self.basis,
            "references": [asdict(r) for r in self.references],
        }
        sidecar.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Shortcut creation ─────────────────────────────────────────────────

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Strip characters illegal in Windows filenames.

        Args:
            name: Raw display name.

        Returns:
            Sanitised filename string (without extension).
        """
        return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")[:80] or "reference"

    @staticmethod
    def _to_url_link(link: str) -> str:
        r"""Normalise *link* to a URL suitable for a ``.url`` shortcut.

        Local Windows paths (``C:\...``) are converted to ``file:///`` URLs.
        Everything else is returned as-is.

        Args:
            link: Raw link value from the form.

        Returns:
            URL string.
        """
        link = link.strip()
        if link.startswith(("http://", "https://", "file://", "ftp://")):
            return link
        # Local path — convert to file:// URL
        p = Path(link)
        return p.as_uri()

    def create_shortcuts(self, kdf_path: Path) -> tuple[int, Path]:
        """Create ``.url`` Internet Shortcut files in ``{kdf_dir}/reference/``.

        Each reference with a non-empty link gets a shortcut.  If two
        references would produce the same filename a numeric suffix is appended
        (``name_2.url``, ``name_3.url``, …).

        Args:
            kdf_path: Path to the .kdf file; shortcuts go into
                ``kdf_path.parent / "reference"``.

        Returns:
            Tuple ``(count_created, reference_folder_path)``.
        """
        ref_dir = kdf_path.parent / "reference"
        ref_dir.mkdir(exist_ok=True)

        created = 0
        used_names: set[str] = set()

        for ref in self.references:
            if not ref.link.strip():
                continue

            base = self._safe_filename(ref.name)
            candidate = base
            suffix = 2
            while candidate.lower() in used_names:
                candidate = f"{base}_{suffix}"
                suffix += 1
            used_names.add(candidate.lower())

            url = self._to_url_link(ref.link)
            content = f"[InternetShortcut]\nURL={url}\n"
            if ref.description:
                # Store description as a comment (ignored by Windows but readable)
                content += f"; {ref.description}\n"

            shortcut_path = ref_dir / f"{candidate}.url"
            shortcut_path.write_text(content, encoding="utf-8")
            created += 1

        return created, ref_dir

    # ── Report helper ─────────────────────────────────────────────────────

    def to_dataframe(self) -> Any:
        """Return a pandas DataFrame for inclusion in the Excel report.

        Returns:
            DataFrame with columns: Name, Category, Link, Description.
        """
        import pandas as pd

        rows = [
            {
                "Name": r.name,
                "Category": r.category,
                "Link": r.link,
                "Description": r.description,
            }
            for r in self.references
        ]
        return pd.DataFrame(rows, columns=["Name", "Category", "Link", "Description"])

    # ── Mutations ─────────────────────────────────────────────────────────

    def add(self, ref: Reference) -> None:
        """Append a new reference.

        Args:
            ref: Reference to add.
        """
        self.references.append(ref)

    def update(self, ref_id: str, **kwargs: Any) -> bool:
        """Update fields on an existing reference by ID.

        Args:
            ref_id: UUID hex of the reference to update.
            **kwargs: Field name → new value.

        Returns:
            True if a matching reference was found and updated, False otherwise.
        """
        for ref in self.references:
            if ref.id == ref_id:
                for k, v in kwargs.items():
                    if hasattr(ref, k):
                        setattr(ref, k, v)
                return True
        return False

    def delete(self, ref_id: str) -> bool:
        """Remove a reference by ID.

        Args:
            ref_id: UUID hex of the reference to remove.

        Returns:
            True if found and removed, False otherwise.
        """
        before = len(self.references)
        self.references = [r for r in self.references if r.id != ref_id]
        return len(self.references) < before

    def get(self, ref_id: str) -> Reference | None:
        """Look up a reference by ID.

        Args:
            ref_id: UUID hex.

        Returns:
            Reference if found, else None.
        """
        return next((r for r in self.references if r.id == ref_id), None)
