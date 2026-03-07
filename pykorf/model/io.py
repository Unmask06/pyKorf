"""I/O and export functionality for KORF models.

This module provides the :class:`IOMixin` which adds save/export/import capabilities
to a model class. It assumes the following attributes/methods exist in the class
that uses this mixin:

- ``self._parser``: A KdfParser instance (for save operations)
- ``self.path``: Property returning the model file path
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykorf.model import Model

_logger = logging.getLogger(__name__)


class IOMixin:
    """Mixin providing I/O and export functionality.

    This mixin assumes the host class provides:
    - ``_parser``: KdfParser instance
    - ``path``: Property returning the model file path
    """

    def save(self, path: str | Path | None = None, *, check_layout: bool = True) -> None:
        """Serialise the (possibly modified) model back to a .kdf file.

        Parameters
        ----------
        path:
            Destination path.  If *None*, overwrites the source file.
        check_layout:
            If True (default), validate layout before saving and warn about
            overlapping elements or elements outside bounds.
        """
        if check_layout:
            from pykorf.model.layout import check_layout as _check_layout

            issues = _check_layout(self)  # type: ignore[arg-type]
            if issues:
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Layout issues detected ({len(issues)}): "
                    "Run model.auto_layout() to fix, or save with check_layout=False to ignore"
                )
                for issue in issues[:5]:  # Log first 5
                    logger.warning(f"  - {issue}")
        print(f"Saving model to {path or self._parser.path}...")  # type: ignore[attr-defined]
        self._parser.save(path)  # type: ignore[attr-defined]

    def save_as(self, path: str | Path, *, check_layout: bool = True) -> None:
        """Save to a new path (alias for :meth:`save` with a path argument)."""
        self.save(path, check_layout=check_layout)

    def to_dataframes(self) -> dict:
        """Convert the model to a dict of DataFrames (one per element type).

        Each DataFrame preserves the raw KDF record lines so that the model
        can be perfectly reconstructed.  Verbatim / header lines are stored
        in a ``"_HEADER"`` DataFrame.

        Returns:
            ``dict[str, pd.DataFrame]`` keyed by element type name.

        Raises:
            ExportError: If *pandas* is not installed.

        Example:
            ```python
            model = Model("Pumpcases.kdf")
            dfs = model.to_dataframes()
            for name, df in dfs.items():
                print(name, len(df))
            ```
        """
        from pykorf.model.export import model_to_dataframes

        return model_to_dataframes(self)

    @classmethod
    def from_dataframes(cls, dfs: dict) -> Model:
        """Create a Model from a dict of DataFrames.

        This is the inverse of :meth:`to_dataframes`.

        Args:
            dfs: Dict of DataFrames as returned by :meth:`to_dataframes`.

        Returns:
            A new :class:`Model` instance.

        Example:
            ```python
            dfs = model.to_dataframes()
            reconstructed = Model.from_dataframes(dfs)
            ```
        """
        from .export import model_from_dataframes

        return model_from_dataframes(dfs)

    def to_excel(self, path: str | Path) -> None:
        """Export the model to an Excel workbook with lossless round-trip fidelity.

        Each element type is written to a separate sheet.  The workbook
        can be read back with :meth:`from_excel` to produce an identical
        ``.kdf`` file.

        Args:
            path: Destination ``.xlsx`` file path.

        Raises:
            ExportError: If *pandas* or *openpyxl* is not installed.

        Example:
            ```python
            model = Model("Pumpcases.kdf")
            model.to_excel("Pumpcases.xlsx")
            ```
        """
        from pykorf.model.export import dataframes_to_excel, model_to_dataframes

        dfs = model_to_dataframes(self)  # type: ignore[arg-type]
        dataframes_to_excel(dfs, path)

    @classmethod
    def from_excel(cls, path: str | Path) -> Model:
        """Create a Model from an Excel workbook.

        This is the inverse of :meth:`to_excel`.

        Args:
            path: Path to the ``.xlsx`` file.

        Returns:
            A new :class:`Model` instance.

        Example:
            ```python
            model = Model.from_excel("Pumpcases.xlsx")
            model.save("Pumpcases_roundtrip.kdf")
            ```
        """
        from pykorf.model.export import excel_to_dataframes, model_from_dataframes

        dfs = excel_to_dataframes(path)
        return model_from_dataframes(dfs)
