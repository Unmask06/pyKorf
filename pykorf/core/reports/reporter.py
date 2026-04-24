from __future__ import annotations

import logging
import re
from typing import Protocol, runtime_checkable

import pandas as pd

from pykorf import Model
from pykorf.core.reports.unit_converter import UnitConverter

_logger = logging.getLogger(__name__)


@runtime_checkable
class Reporter(Protocol):
    """Interface for extracting model data into DataFrames for report generation.

    Implementations provide data from different sources:
    - PykorfReporter: extracts from KDF file via Model (current behaviour)
    - KorfReporter: extracts results from KORF Excel report + input data from Model
    """

    def generate_dataframes(self) -> dict[str, pd.DataFrame]:
        """Return a dict mapping sheet names to DataFrames of element data."""
        ...

    def get_validation_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame with columns: Severity, Category, Element, Message."""
        ...

    def get_model_title(self) -> str:
        """Return the model title string."""
        ...

    def get_source_name(self) -> str:
        """Return the source file name for display."""
        ...

    def get_case_names(self) -> list[str]:
        """Return list of case names."""
        ...

    def generate_all_case_dataframes(self) -> dict[str, dict[str, pd.DataFrame]]:
        """Return dict mapping case name to dict of element DataFrames.

        For single-case reporters (PykorfReporter), the dict has one entry
        keyed by case name. For multi-case reporters (KorfReporter), there
        is one entry per KORF case.
        """
        ...

    @property
    def basis(self) -> str:
        ...

    @property
    def remarks(self) -> str:
        ...

    @property
    def hold(self) -> str:
        ...

    @property
    def references(self) -> list[dict]:
        ...


_SEVERITY_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"fails sizing|exceeds criteria|mismatch", re.I), "Error"),
    (re.compile(r"references pipe index .+ which does not exist", re.I), "Error"),
    (
        re.compile(r"missing line number|missing NAME|missing CON|missing|not found in PMS", re.I),
        "Warning",
    ),
    (re.compile(r"Add Title", re.I), "Info"),
    (re.compile(r"pipe.*criteria", re.I), "Error"),
    (re.compile(r"CONN|connectiv|nozzle|CON value", re.I), "Error"),
]


def _classify_issue(msg: str) -> tuple[str, str, str]:
    """Classify a validation message into (severity, category, element_name)."""
    from pykorf.app.validation import classify_issue

    elem_name = ""
    for pat in [
        re.compile(r"Pipe ['\"]?(\S+?)['\"]?[:\s]"),
        re.compile(r"PIPE (\S+?) \("),
        re.compile(r"^(\S+?) \((?:VALVE|PUMP|FEED|PRODUCT|COMPRESSOR|TEE|JUNC|VESSEL)\)"),
    ]:
        m = pat.search(msg)
        if m:
            elem_name = m.group(1)
            break

    category = classify_issue(msg)

    for pattern, severity in _SEVERITY_RULES:
        if pattern.search(msg):
            return severity, category, elem_name

    return "Warning", category, elem_name


class PykorfReporter:
    """Extracts element data from a pyKorf Model (KDF file) for report generation.

    This is the original data extraction logic, now cleanly separated from
    the ReportExporter formatting/layout code.
    """

    def __init__(
        self,
        model: Model,
        basis: str = "",
        remarks: str = "",
        hold: str = "",
        references: list[dict] | None = None,
        justifications: dict[str, str] | None = None,
    ):
        self.model = model
        self._basis = basis
        self._remarks = remarks
        self._hold = hold
        self._references = references or []
        self._justifications = justifications or {}
        self._converter = UnitConverter()

        self._extractors = {
            "Feeds": self._extract_feeds,
            "Products": self._extract_products,
            "Pipes": self._extract_pipes,
            "Pumps": self._extract_pumps,
            "Compressors": self._extract_compressors,
            "Valves": self._extract_valves,
            "Heat Exchangers": self._extract_heat_exchangers,
            "Junctions": self._extract_junctions,
            "Misc Equipment": self._extract_misc,
        }

    @property
    def basis(self) -> str:
        return self._basis

    @property
    def remarks(self) -> str:
        return self._remarks

    @property
    def hold(self) -> str:
        return self._hold

    @property
    def references(self) -> list[dict]:
        return self._references

    def get_model_title(self) -> str:
        """Fetches the model title from SYMBOL records with TYPE='Text' and FSIZ=2."""
        from pykorf.core.elements import Symbol

        symbol_indices = {
            rec.index
            for rec in self.model._parser.records
            if rec.element_type == "SYMBOL" and rec.index is not None
        }
        for idx in symbol_indices:
            type_rec = self.model._parser.get("SYMBOL", idx, Symbol.TYPE)
            fsiz_rec = self.model._parser.get("SYMBOL", idx, Symbol.FSIZ)
            text_rec = self.model._parser.get("SYMBOL", idx, Symbol.TEXT)
            if not (type_rec and fsiz_rec and text_rec):
                continue
            try:
                if type_rec.values[0] == "Text" and int(fsiz_rec.values[0]) == 2:
                    return str(text_rec.values[0]) if text_rec.values else ""
            except (ValueError, TypeError, IndexError):
                continue
        return ""

    def get_source_name(self) -> str:
        """Return the KDF file name."""
        from pathlib import Path

        return Path(self.model._parser.path).name

    def get_case_names(self) -> list[str]:
        """Return case descriptions from the model."""
        return self.model.general.case_descriptions if hasattr(self.model, "general") else []

    def generate_all_case_dataframes(self) -> dict[str, dict[str, pd.DataFrame]]:
        """Return single-case DataFrames keyed by case description."""
        case_names = self.get_case_names()
        key = case_names[0] if case_names else ""
        return {key: self.generate_dataframes()}

    def generate_dataframes(self) -> dict[str, pd.DataFrame]:
        """Runs all registered extractors and returns a dictionary of DataFrames."""
        dfs = {}
        for sheet_name, extractor_func in self._extractors.items():
            data = extractor_func()
            if data:
                converted_data = self._converter.convert_summary(data)
                dfs[sheet_name] = pd.DataFrame(converted_data)
        return dfs

    def get_validation_dataframe(self) -> pd.DataFrame:
        """Run all model validation checks, return a structured DataFrame."""
        issues: list[dict[str, str]] = []

        try:
            for msg in self.model.validate():
                severity, category, elem = _classify_issue(msg)
                issues.append(
                    {
                        "Severity": severity,
                        "Category": category,
                        "Element": elem,
                        "Message": msg,
                    }
                )
        except Exception as exc:
            _logger.warning("validation failed: %s", exc)

        if self._justifications:
            for pipe_name, justification in self._justifications.items():
                issues.append(
                    {
                        "Severity": "Justified",
                        "Category": "Criteria",
                        "Element": pipe_name,
                        "Message": f"Pipe '{pipe_name}': criteria violation justified - {justification}",
                    }
                )

        if not issues:
            return pd.DataFrame(columns=["Severity", "Category", "Element", "Message"])
        return pd.DataFrame(issues)

    # =========================================================
    # ELEMENT EXTRACTORS
    # =========================================================

    def _extract_pipes(self) -> list[dict]:
        return [
            pipe.summary(export=True, justifications=self._justifications)
            for idx, pipe in self.model.pipes.items()
            if idx != 0 and not pipe.name.startswith("d")
        ]

    def _extract_pumps(self) -> list[dict]:
        return [
            pump.summary(export=True, model=self.model)
            for idx, pump in self.model.pumps.items()
            if idx != 0
        ]

    def _extract_compressors(self) -> list[dict]:
        return [
            comp.summary(export=True) for idx, comp in self.model.compressors.items() if idx != 0
        ]

    def _extract_feeds(self) -> list[dict]:
        return [feed.summary(export=True) for idx, feed in self.model.feeds.items() if idx != 0]

    def _extract_products(self) -> list[dict]:
        return [prod.summary(export=True) for idx, prod in self.model.products.items() if idx != 0]

    def _extract_valves(self) -> list[dict]:
        return [
            valve.summary(export=True, model=self.model)
            for idx, valve in self.model.valves.items()
            if idx != 0
        ]

    def _extract_heat_exchangers(self) -> list[dict]:
        return [hx.summary(export=True) for idx, hx in self.model.exchangers.items() if idx != 0]

    def _extract_junctions(self) -> list[dict]:
        """Extract junction data for export.

        Only includes junctions whose names do NOT start with 'J'.
        """
        return [
            junction.summary(export=True)
            for idx, junction in self.model.junctions.items()
            if idx != 0 and not junction.name.startswith("J")
        ]

    def _extract_misc(self) -> list[dict]:
        return [
            misc.summary(export=True)
            for idx, misc in self.model.misc_equipment.items()
            if idx != 0
        ]
