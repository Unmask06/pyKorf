"""Core Model class for KORF .kdf hydraulic model files.

This module provides the base Model class that serves as the primary API
for loading, manipulating, and saving KORF hydraulic models. The Model
class manages in-memory element collections and coordinates with the
KdfParser for file I/O operations.

All element collections (pipes, pumps, feeds, etc.) are lazily constructed
from the KdfParser record list and exposed as integer-indexed dicts.
Index 0 is the default template; real instances start at 1.

Persistence boundary:
    All Model manipulations are in-memory only. The loaded source file is
    not modified until save() or save_as() is called.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pykorf.elements import (
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
from pykorf.exceptions import ElementNotFound
from pykorf.parser import KdfParser

_DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "library" / "New.kdf"

_logger = logging.getLogger(__name__)


class _ModelBase:
    """Base class for KORF .kdf hydraulic model (extended via mixins).

    This class provides the core functionality and is composed with mixins
    in the model subpackage's __init__.py to create the final Model class.

    Args:
        path: Path to a ``.kdf`` file. If ``None``, a blank model is created
            from the default ``New.kdf`` template.

    Example:
        ```python
        model = Model()  # blank from defaults
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

    @classmethod
    def load(cls, path: str | Path) -> _ModelBase:
        """Load a .kdf file and return a :class:`Model`."""
        return cls(path)

    def _build_collections(self) -> None:
        """Populate element dict-of-dicts from the parser records."""
        self.general = General(self._parser)

        self.pipes: dict[int, Pipe] = self._build(Element.PIPE, Pipe)
        self.feeds: dict[int, Feed] = self._build(Element.FEED, Feed)
        self.products: dict[int, Product] = self._build(Element.PROD, Product)
        self.pumps: dict[int, Pump] = self._build(Element.PUMP, Pump)
        self.valves: dict[int, Valve] = self._build(Element.VALVE, Valve)
        self.check_valves: dict[int, CheckValve] = self._build(Element.CHECK, CheckValve)
        self.orifices: dict[int, FlowOrifice] = self._build(Element.ORIFICE, FlowOrifice)
        self.exchangers: dict[int, HeatExchanger] = self._build(Element.HX, HeatExchanger)
        self.compressors: dict[int, Compressor] = self._build(Element.COMP, Compressor)
        self.misc_equipment: dict[int, MiscEquipment] = self._build(Element.MISC, MiscEquipment)
        self.expanders: dict[int, Expander] = self._build(Element.EXPAND, Expander)
        self.junctions: dict[int, Junction] = self._build(Element.JUNC, Junction)
        self.tees: dict[int, Tee] = self._build(Element.TEE, Tee)
        self.vessels: dict[int, Vessel] = self._build(Element.VESSEL, Vessel)
        self.pipedata: dict[int, PipeData] = self._build(Element.PIPEDATA, PipeData)

        self._rebuild_name_map()

    def _build(self, etype: str, cls) -> dict:
        """Collect all distinct indices for *etype* from the record list.

        Return a dict mapping index -> element object.
        """
        seen = set()
        result = {}
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

    def _all_collections(self) -> list[dict]:
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

    def _collection_for_etype(self, etype: str) -> Any:
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

    def get_element(self, name: str) -> BaseElement:
        """Look up an element by its NAME tag.

        Raises :exc:`ElementNotFound` if no element has that name.
        """
        elem = self._name_map.get(name)
        if elem is None:
            raise ElementNotFound(name)
        return elem

    def __getitem__(self, name: str) -> BaseElement:
        """``model['PIPE1']`` shorthand for :meth:`get_element`."""
        return self.get_element(name)

    def __contains__(self, name: str) -> bool:
        return name in self._name_map

    @property
    def path(self) -> Path:
        return self._parser.path

    @property
    def version(self) -> str:
        return self._parser.version()

    @property
    def num_pipes(self) -> int:
        return self._parser.num_instances("PIPE")

    @property
    def num_pumps(self) -> int:
        return self._parser.num_instances("PUMP")

    @property
    def num_cases(self) -> int:
        return self.general.num_cases

    @property
    def elements(self) -> list[BaseElement]:
        """Return all real element instances (index >= 1) across all types."""
        result: list[BaseElement] = []
        for collection in self._all_collections():
            for idx, elem in sorted(collection.items()):
                if idx >= 1:
                    result.append(elem)
        return result

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
