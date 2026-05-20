"""KORF Model — primary API for loading, manipulating, and saving hydraulic models.

This package provides service classes that encapsulate specific domain operations
for KORF hydraulic models. Each service focuses on a specific aspect of model
manipulation and is designed to be used through the main Model API.

Available Services:
    - ElementService: CRUD operations for model elements (create, update, delete, copy)
    - QueryService: Element querying and parameter access with filtering capabilities
    - ConnectivityService: Managing connections between elements (pipes, equipment, etc.)
    - LayoutService: Element positioning, auto-placement, and layout visualization
    - IOService: File I/O operations including save, export to Excel/DataFrames
    - SummaryService: Model summary and statistical information generation

All element collections (pipes, pumps, feeds, etc.) are constructed from the
KdfParser record list and exposed as integer-indexed dicts.
Index 0 is the default template; real instances start at 1.

Persistence boundary:
    All Model manipulations are in-memory only. The loaded source file is
    not modified until save() or save_as() is called.

Example:
    Services are typically accessed via the Model instance::

        from pykorf import Model
        model = Model("example.kdf")

        # Element operations
        model.add_element("PUMP", "P1", {"EFFP": 0.75})

        # Query operations
        pipes = model.get_elements(etype="PIPE", name="L*")

        # Connectivity operations
        model.connect_elements("L1", "P1")

        # Layout operations
        model.auto_place(element)

        # I/O operations
        model.save()
        model.to_excel("export.xlsx")

        # Summary operations
        model.get_summary()
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any

from pykorf.core.elements import (
    BaseElement,
    CheckValve,
    Compressor,
    Element,
    Expander,
    Feed,
    FlowOrifice,
    General,
    HeatExchanger,
    Junction,
    MiscEquipment,
    Pipe,
    PipeData,
    Product,
    Pump,
    Tee,
    Valve,
    Vessel,
)
from pykorf.core.exceptions import ElementNotFound
from pykorf.core.model.connectivity import ConnectivityService
from pykorf.core.model.core import ElementCollection, _DEFAULT_TEMPLATE
from pykorf.core.model.element import ElementService
from pykorf.core.model.io import IOService
from pykorf.core.model.layout import LayoutService
from pykorf.core.model.query import QueryService
from pykorf.core.model.summary import SummaryService
from pykorf.core.parser import KdfParser

__all__ = [
    "ConnectivityService",
    "ElementService",
    "IOService",
    "LayoutService",
    "Model",
    "QueryService",
    "SummaryService",
]

_logger = logging.getLogger(__name__)


class Model:
    """Main entry point for working with KORF .kdf hydraulic models.

    The Model class manages in-memory element collections and coordinates
    with the KdfParser for file I/O.  Feature-specific behaviour is
    delegated to internal service objects (element, query, connectivity,
    layout, I/O, summary).

    Args:
        path: Path to a ``.kdf`` file.  If ``None``, a blank model is
            created from the default ``New.kdf`` template.

    Example:
        ```python
        model = Model()              # blank from defaults
        model = Model("Pumpcases.kdf")  # load existing file
        ```
    """

    def __init__(self, path: str | Path | None = None):
        if path is None:
            path = _DEFAULT_TEMPLATE
        self._parser = KdfParser(path)
        _logger.info("── Load Model ── %s", self._parser.path.name)
        self._parser.load()
        self._build_collections()
        self._loaded_mtime = self._parser.path.stat().st_mtime
        _logger.info(
            "   Model ready | pipes=%d  pumps=%d  feeds=%d  products=%d  valves=%d  compressors=%d",
            self._parser.num_instances("PIPE"),
            self._parser.num_instances("PUMP"),
            self._parser.num_instances("FEED"),
            self._parser.num_instances("PROD"),
            self._parser.num_instances("VALVE"),
            self._parser.num_instances("COMP"),
        )
        # Initialize service instances bound to this model
        self._element_service = ElementService(self)
        self._query_service = QueryService(self)
        self._connectivity_service = ConnectivityService(self)
        self._layout_service = LayoutService(self)
        self._io_service = IOService(self)
        self._summary_service = SummaryService(self, self._parser.path if self._parser else None)

    @classmethod
    def load(cls, path: str | Path) -> Model:
        """Load a .kdf file and return a :class:`Model`."""
        return cls(path)

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def _build_collections(self) -> None:
        """Populate element dict-of-dicts from the parser records."""
        self.general = General(self._parser)

        self.pipes: ElementCollection[Pipe] = self._build(Element.PIPE, Pipe)
        self.feeds: ElementCollection[Feed] = self._build(Element.FEED, Feed)
        self.products: ElementCollection[Product] = self._build(Element.PROD, Product)
        self.pumps: ElementCollection[Pump] = self._build(Element.PUMP, Pump)
        self.valves: ElementCollection[Valve] = self._build(Element.VALVE, Valve)
        self.check_valves: ElementCollection[CheckValve] = self._build(Element.CHECK, CheckValve)
        self.orifices: ElementCollection[FlowOrifice] = self._build(Element.ORIFICE, FlowOrifice)
        self.exchangers: ElementCollection[HeatExchanger] = self._build(Element.HX, HeatExchanger)
        self.compressors: ElementCollection[Compressor] = self._build(Element.COMP, Compressor)
        self.misc_equipment: ElementCollection[MiscEquipment] = self._build(
            Element.MISC, MiscEquipment
        )
        self.expanders: ElementCollection[Expander] = self._build(Element.EXPAND, Expander)
        self.junctions: ElementCollection[Junction] = self._build(Element.JUNC, Junction)
        self.tees: ElementCollection[Tee] = self._build(Element.TEE, Tee)
        self.vessels: ElementCollection[Vessel] = self._build(Element.VESSEL, Vessel)
        self.pipedata: ElementCollection[PipeData] = self._build(Element.PIPEDATA, PipeData)

        self._rebuild_name_map()

    def _build(self, etype: str, cls: type[Any]) -> ElementCollection[Any]:
        """Collect all distinct indices for *etype* from the record list.

        Return a dict mapping index -> element object.
        """
        seen = set()
        result: ElementCollection[Any] = ElementCollection()
        for rec in self._parser.records:
            if rec.element_type == etype and rec.index not in seen:
                seen.add(rec.index)
                result[rec.index] = cls(self._parser, rec.index)
        return result

    def _rebuild_name_map(self) -> None:
        """Rebuild the ``name -> element`` mapping from all collections."""
        self._name_map: dict[str, BaseElement] = {}
        for collection in self._all_collections():
            for elem in collection.values():
                if elem.index == 0:
                    continue
                name = elem.name
                if name:
                    self._name_map[name] = elem

    def _all_collections(self) -> list[ElementCollection[Any]]:
        """Return all element collection dicts."""
        return [
            self.pipes,
            self.feeds,
            self.products,
            self.pumps,
            self.valves,
            self.check_valves,
            self.orifices,
            self.exchangers,
            self.compressors,
            self.misc_equipment,
            self.expanders,
            self.junctions,
            self.tees,
            self.vessels,
            self.pipedata,
        ]

    def _collection_for_etype(self, etype: str) -> ElementCollection[Any] | None:
        """Return the collection dict for a given element type keyword."""
        et = etype.upper()
        if et == Element.PIPE:
            return self.pipes
        if et == Element.FEED:
            return self.feeds
        if et == Element.PROD:
            return self.products
        if et == Element.PUMP:
            return self.pumps
        if et == Element.VALVE:
            return self.valves
        if et == Element.CHECK:
            return self.check_valves
        if et == Element.ORIFICE:
            return self.orifices
        if et == Element.HX:
            return self.exchangers
        if et == Element.COMP:
            return self.compressors
        if et == Element.MISC:
            return self.misc_equipment
        if et == Element.EXPAND:
            return self.expanders
        if et == Element.JUNC:
            return self.junctions
        if et == Element.TEE:
            return self.tees
        if et == Element.VESSEL:
            return self.vessels
        if et == Element.PIPEDATA:
            return self.pipedata
        return None

    def _ensure_unique_name(self, name: str, current_name: str | None = None) -> str:
        """Return a unique name; if *name* already exists, append "_1", "_2", etc.

        Parameters
        name:
            Desired element name.
        current_name:
            Current name of element being renamed.

        Returns:
            Original *name* if unique, or modified version with suffix.
        """
        if len(name) > 12:
            raise ValueError(f"Element name {name!r} exceeds 12 character limit")

        existing = self._name_map.get(name)
        if existing is None:
            return name
        if current_name is not None and name == current_name:
            return name

        suffix_num = 1
        while True:
            unique_name = f"{name}_{suffix_num}"
            if len(unique_name) > 12:
                raise ValueError(f"Generated name {unique_name!r} for {name!r} exceeds 12 chars")
            if unique_name not in self._name_map:
                _logger.info("Element name '%s' exists, using '%s'", name, unique_name)
                return unique_name
            suffix_num += 1

    # ------------------------------------------------------------------
    # Element lookup
    # ------------------------------------------------------------------

    def get_element(self, name: str, etype: str | None = None) -> Any:
        """Look up an element by name, optionally narrowing by type.

        Args:
            name: Element NAME tag.
            etype: Optional element type to narrow the search.

        Raises:
            ElementNotFound: If no element with the given name exists.
        """
        return self._query_service.get_element(name, etype)

    def __getitem__(self, name: str) -> BaseElement:
        """``model['PIPE1']`` shorthand for :meth:`get_element`."""
        return self.get_element(name)

    def __contains__(self, name: str) -> bool:
        return name in self._name_map

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._parser.path

    @property
    def version(self) -> str:
        return self._parser.version()

    @property
    def elements(self) -> list[BaseElement]:
        """Return all real element instances (index >= 1) across all types."""
        result: list[BaseElement] = []
        for collection in self._all_collections():
            for idx, elem in sorted(collection.items()):
                if idx >= 1:
                    result.append(elem)
        return result

    # ------------------------------------------------------------------
    # Deprecated num_* properties
    # ------------------------------------------------------------------

    @property
    def num_pipes(self) -> int:
        warnings.warn(
            "model.num_pipes is deprecated, use len(model.pipes) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.pipes)

    @property
    def num_pumps(self) -> int:
        warnings.warn(
            "model.num_pumps is deprecated, use len(model.pumps) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.pumps)

    @property
    def num_junctions(self) -> int:
        warnings.warn(
            "model.num_junctions is deprecated, use len(model.junctions) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.junctions)

    @property
    def num_cases(self) -> int:
        warnings.warn(
            "model.num_cases is deprecated, use model.general.num_cases instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.general.num_cases

    @property
    def num_feeds(self) -> int:
        warnings.warn(
            "model.num_feeds is deprecated, use len(model.feeds) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.feeds)

    @property
    def num_products(self) -> int:
        warnings.warn(
            "model.num_products is deprecated, use len(model.products) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.products)

    @property
    def num_valves(self) -> int:
        warnings.warn(
            "model.num_valves is deprecated, use len(model.valves) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.valves)

    @property
    def num_compressors(self) -> int:
        warnings.warn(
            "model.num_compressors is deprecated, use len(model.compressors) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.compressors)

    @property
    def num_orifices(self) -> int:
        warnings.warn(
            "model.num_orifices is deprecated, use len(model.orifices) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.orifices)

    @property
    def num_exchangers(self) -> int:
        warnings.warn(
            "model.num_exchangers is deprecated, use len(model.exchangers) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.exchangers)

    @property
    def num_check_valves(self) -> int:
        warnings.warn(
            "model.num_check_valves is deprecated, use len(model.check_valves) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.check_valves)

    @property
    def num_misc_equipment(self) -> int:
        warnings.warn(
            "model.num_misc_equipment is deprecated, use len(model.misc_equipment) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.misc_equipment)

    @property
    def num_expanders(self) -> int:
        warnings.warn(
            "model.num_expanders is deprecated, use len(model.expanders) instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(self.expanders)

    # ------------------------------------------------------------------
    # Element operations (delegate to _element_service)
    # ------------------------------------------------------------------

    def add_element(self, etype: str, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._element_service.add_element(etype, name, params)

    def add_elements(self, elements: list[tuple[str, str, dict[str, Any]]]) -> list[Any]:
        return self._element_service.add_elements(elements)

    def update_element(self, name: str, params: dict[str, Any]) -> None:
        return self._element_service.update_element(name, params)

    def update_elements(self, updates: dict[str, dict[str, Any]]) -> None:
        return self._element_service.update_elements(updates)

    def delete_element(self, name: str) -> None:
        return self._element_service.delete_element(name)

    def delete_elements(self, names: list[str]) -> None:
        return self._element_service.delete_elements(names)

    def copy_element(self, name: str, new_name: str | None = None) -> Any:
        return self._element_service.copy_element(name, new_name)

    def move_element(self, name: str, new_index: int) -> None:
        return self._element_service.move_element(name, new_index)

    # ------------------------------------------------------------------
    # Query operations (delegate to _query_service)
    # ------------------------------------------------------------------

    def get_elements(self, etype: str | None = None, name: str | None = None) -> list[Any]:
        return self._query_service.get_elements(etype, name)

    def get_elements_by_type(self, etype: str) -> list[Any]:
        return self._query_service.get_elements_by_type(etype)

    def set_param(self, name: str, param: str, value: Any) -> None:
        return self._query_service.set_params(name, {param: value})

    def set_params(self, name: str, params: dict[str, Any]) -> None:
        return self._query_service.set_params(name, params)

    def get_param(self, name: str, param: str) -> Any:
        record = self._query_service.get_params(name, param)
        return record.values[0] if record.values else None

    def get_params(self, name: str) -> dict[str, Any]:
        records = self._query_service.get_params(name)  # type: ignore[assignment]
        if isinstance(records, dict):
            return {
                k: (v.values[0] if len(v.values) == 1 else v.values) for k, v in records.items()
            }
        return {}

    # ------------------------------------------------------------------
    # Connectivity operations (delegate to _connectivity_service)
    # ------------------------------------------------------------------

    def connect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str] | tuple[str, str, str]],
        name2: str | None = None,
        pipe_name: str | None = None,
    ) -> None:
        return self._connectivity_service.connect_elements(name1_or_pairs, name2, pipe_name)

    def disconnect_elements(self, element1: str, element2: str) -> None:
        return self._connectivity_service.disconnect_elements(element1, element2)

    # ------------------------------------------------------------------
    # Layout operations (delegate to _layout_service)
    # ------------------------------------------------------------------

    def auto_place(self, element: Any) -> None:
        return self._layout_service.auto_place(element)

    def check_layout(self) -> list[str]:
        return self._layout_service.check_layout()

    # ------------------------------------------------------------------
    # I/O operations (delegate to _io_service)
    # ------------------------------------------------------------------

    def save(self, path: str | Path | None = None, *, overwrite: bool = True) -> None:
        return self._io_service.save(path, overwrite=overwrite)

    def save_as(self, path: str | Path, *, overwrite: bool = False) -> None:
        return self._io_service.save_as(path, overwrite=overwrite)

    def to_excel(self, path: str | Path) -> None:
        self._io_service.to_excel(path)

    def to_dataframes(self) -> dict[str, Any]:
        return self._io_service.to_dataframes()

    def from_excel(self, path: str | Path) -> None:
        return self._io_service.from_excel(path)

    def from_dataframes(self, data: dict[str, Any]) -> None:
        return self._io_service.from_dataframes(data)

    # ------------------------------------------------------------------
    # Summary operations (delegate to _summary_service)
    # ------------------------------------------------------------------

    def get_summary(self) -> dict[str, Any]:
        return self._summary_service.summary()

    def validate(self) -> list[str]:
        """Run all validation checks (core + app-level + connectivity).

        Combines three layers:
        1. Core KDF-format checks (pipe sizing criteria, title symbol)
        2. App-level checks (PMS spec, line-number parsing, pipe properties)
        3. Connectivity checks (dangling references, unconnected elements)

        Returns:
            List of human-readable issue descriptions.
        """
        issues: list[str] = []
        # Core: pipe sizing criteria + title symbol
        issues.extend(self._summary_service.validate())
        # App: PMS, line numbers, pipe properties vs spec
        try:
            from pykorf.app.validation import validate as _app_validate

            issues.extend(_app_validate(self))
        except ImportError:
            pass  # App-level validation skipped (pure core usage)
        # Connectivity: dangling pipe references, unconnected elements
        issues.extend(self._connectivity_service.check_connectivity())
        return issues

    def __repr__(self) -> str:
        return self._summary_service.__repr__()

    # ------------------------------------------------------------------
    # Internal methods (for advanced / service usage)
    # ------------------------------------------------------------------

    def _add_element_internal(
        self,
        etype: str,
        name: str,
        params: dict[str, Any] | None = None,
        auto_position: bool = True,
    ) -> Any:
        return self._element_service._add_element_internal(
            etype, name, params, auto_position=auto_position
        )

    def _next_auto_pipe_name(self) -> str:
        return self._element_service._next_auto_pipe_name()

    def _position_pipe_between(self, pipe_name: str, name1: str, name2: str) -> None:
        return self._element_service._position_pipe_between(pipe_name, name1, name2)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def is_file_modified(self) -> bool:
        """Check if the file has been modified since it was loaded.

        Returns:
            True if the file's modification time has changed since loading,
            False otherwise.
        """
        try:
            current_mtime = self._parser.path.stat().st_mtime
            return current_mtime != self._loaded_mtime
        except FileNotFoundError:
            return False

    def reload(self) -> None:
        """Reload the model from disk.

        This method re-reads the .kdf file from disk and rebuilds all
        in-memory collections. Useful when the file has been modified
        externally (e.g., via KORF GUI) while the model is loaded in TUI.

        Raises:
            ParseError: If the file cannot be read or parsed.
        """
        _logger.info("── Reload Model ── %s", self._parser.path.name)
        self._parser.load()
        self._build_collections()
        self._loaded_mtime = self._parser.path.stat().st_mtime
        _logger.info("   Reload complete | %s", self._parser.path.name)
