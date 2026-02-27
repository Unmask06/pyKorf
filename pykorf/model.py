"""KorfModel / Model – top-level container for a KORF .kdf file.

All element collections (pipes, pumps, feeds …) are lazily constructed
from the :class:`KdfParser` record list and exposed as integer-indexed
dicts.  Index 0 is the default template; real instances start at 1.

Persistence boundary:
all Model manipulations are in-memory only. The loaded source file is not
modified until :meth:`save` or :meth:`save_as` is called.

Basic workflow::

    from pykorf import Model

    # Create blank model from defaults
    model = Model()

    # … or load an existing file
    model = Model("Pumpcases.kdf")

    # Inspect
    print(model.general.case_descriptions)
    print(model["L1"].get_flow())

    # Edit by name
    model.update_element("L1", {"LEN": 200, "TFLOW": "80;90;60"})

    # Add / delete / copy
    model.add_element("PIPE", "L10", {"LEN": 50})
    model.delete_element("L10")
    model.copy_element("L1", "L11")

    # Save
    model.save("Pumpcases_new.kdf")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pykorf.definitions.element import Element
from pykorf.elements import (
    ELEMENT_REGISTRY,
    BaseElement,
    CheckValve,
    Compressor,
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

# Path to the bundled default template
_DEFAULT_TEMPLATE = Path(__file__).resolve().parent / "library" / "New.kdf"

# Logger for model operations
_logger = logging.getLogger(__name__)


class Model:
    """In-memory representation of a KORF .kdf hydraulic model file.

    Parameters
    ----------
    path:
        Path to a ``.kdf`` file.  If *None*, a blank model is created
        from the default ``New.kdf`` template.

    Examples:
    --------
    >>> model = Model()  # blank from defaults
    >>> model = Model("Pumpcases.kdf")  # load existing file
    """

    def __init__(self, path: str | Path | None = None):
        if path is None:
            path = _DEFAULT_TEMPLATE
        self._parser = KdfParser(path)
        self._parser.load()
        self._build_collections()

    # ------------------------------------------------------------------
    # Class constructors (backward compatibility)
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> Model:
        """Load a .kdf file and return a :class:`Model`."""
        return cls(path)

    # ------------------------------------------------------------------
    # Build element collections
    # ------------------------------------------------------------------

    def _build_collections(self) -> None:
        """Populate element dict-of-dicts from the parser records."""
        # General (always index 0, single instance)
        self.general = General(self._parser)

        # Build typed collections for element types that have instances
        self.pipes: dict[int, Pipe] = self._build("PIPE", Pipe)
        self.feeds: dict[int, Feed] = self._build("FEED", Feed)
        self.products: dict[int, Product] = self._build("PROD", Product)
        self.pumps: dict[int, Pump] = self._build("PUMP", Pump)
        self.valves: dict[int, Valve] = self._build("VALVE", Valve)
        self.check_valves: dict[int, CheckValve] = self._build("CHECK", CheckValve)
        self.orifices: dict[int, FlowOrifice] = self._build("FO", FlowOrifice)
        self.exchangers: dict[int, HeatExchanger] = self._build("HX", HeatExchanger)
        self.compressors: dict[int, Compressor] = self._build("COMP", Compressor)
        self.misc_equipment: dict[int, MiscEquipment] = self._build(
            "MISC", MiscEquipment
        )
        self.expanders: dict[int, Expander] = self._build("EXPAND", Expander)
        self.junctions: dict[int, Junction] = self._build("JUNC", Junction)
        self.tees: dict[int, Tee] = self._build("TEE", Tee)
        self.vessels: dict[int, Vessel] = self._build("VESSEL", Vessel)
        self.pipedata: dict[int, PipeData] = self._build("PIPEDATA", PipeData)

        # Name → element lookup
        self._rebuild_name_map()

    def _build(self, etype: str, cls) -> dict:
        """Collect all distinct indices for *etype* from the record list and
        return a dict mapping index → element object.
        """
        seen = set()
        result = {}
        for rec in self._parser.records:
            if rec.element_type == etype and rec.index not in seen:
                seen.add(rec.index)
                result[rec.index] = cls(self._parser, rec.index)
        return result

    # ------------------------------------------------------------------
    # Name-based element lookup
    # ------------------------------------------------------------------

    def _rebuild_name_map(self) -> None:
        """Rebuild the ``name → element`` mapping from all collections."""
        self._name_map: dict[str, BaseElement] = {}
        for collection in self._all_collections():
            for elem in collection.values():
                if elem.index == 0:
                    continue  # skip templates
                name = elem.name
                if name:
                    self._name_map[name] = elem

    def _ensure_unique_name(self, name: str, current_name: str | None = None) -> str:
        """Return a unique name; if *name* already exists, append \"_1\", \"_2\", etc.

        Parameters
        ----------
        name:
            Desired element name.
        current_name:
            Current name of element being renamed (for update scenarios).

        Returns:
        -------
        str
            The original *name* if unique, or a modified version with suffix if a duplicate.
        """
        existing = self._name_map.get(name)
        if existing is None:
            return name
        if current_name is not None and name == current_name:
            return name

        # Generate unique name by appending suffix
        suffix_num = 1
        while True:
            unique_name = f"{name}_{suffix_num}"
            if unique_name not in self._name_map:
                _logger.info(
                    f"Element name '{name}' already exists. Using '{unique_name}' instead."
                )
                return unique_name
            suffix_num += 1

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
        if et == "PIPE":
            return self.pipes
        if et == "FEED":
            return self.feeds
        if et == "PROD":
            return self.products
        if et == "PUMP":
            return self.pumps
        if et == "VALVE":
            return self.valves
        if et == "CHECK":
            return self.check_valves
        if et == "FO":
            return self.orifices
        if et == "HX":
            return self.exchangers
        if et == "COMP":
            return self.compressors
        if et == "MISC":
            return self.misc_equipment
        if et == "EXPAND":
            return self.expanders
        if et == "JUNC":
            return self.junctions
        if et == "TEE":
            return self.tees
        if et == "VESSEL":
            return self.vessels
        if et == "PIPEDATA":
            return self.pipedata
        return None

    def get_element(self, name: str) -> BaseElement:
        """Look up an element by its NAME tag.

        Raises :exc:`ElementNotFound` if no element has that name.
        """
        elem = self._name_map.get(name)
        if elem is None:
            raise ElementNotFound(f"No element named {name!r} in model")
        return elem

    def __getitem__(self, name: str) -> BaseElement:
        """``model['PIPE1']`` shorthand for :meth:`get_element`."""
        return self.get_element(name)

    def __contains__(self, name: str) -> bool:
        return name in self._name_map

    # ------------------------------------------------------------------
    # Elements listing
    # ------------------------------------------------------------------

    @property
    def elements(self) -> list[BaseElement]:
        """Return all real element instances (index >= 1) across all types."""
        result: list[BaseElement] = []
        for collection in self._all_collections():
            for idx, elem in sorted(collection.items()):
                if idx >= 1:
                    result.append(elem)
        return result

    def get_elements_by_type(self, etype: str) -> list[BaseElement]:
        """Return all instances of a given element type (index >= 1).

        Parameters
        ----------
        etype:
            KDF element type keyword, e.g. ``'PIPE'``, ``'PUMP'``, ``'FO'``.
        """
        collection = self._collection_for_etype(etype)
        if collection is None:
            return []
        return [elem for idx, elem in sorted(collection.items()) if idx >= 1]

    # ------------------------------------------------------------------
    # Update element parameters
    # ------------------------------------------------------------------

    def update_element(self, name: str, params: dict[str, Any]) -> None:
        """Update parameters of the named element.

        Parameters
        ----------
        name:
            Element NAME tag (e.g. ``'L1'``, ``'P1'``).
        params:
            Dict of ``{KDF_PARAM: value}``.  Values are set as the first
            token of the record's value list.  Special key ``'X'`` and
            ``'Y'`` update the XY record.

        Example:
        -------
        >>> model.update_element("L1", {"LEN": 200, "TFLOW": "80;90;60"})
        """
        elem = self.get_element(name)
        rebuild_collections = False
        if "NAME" in {key.upper() for key in params}:
            name_key = next(k for k in params if k.upper() == "NAME")
            new_name = str(params[name_key])
            new_name = self._ensure_unique_name(new_name, current_name=elem.name)
            params[name_key] = new_name  # Update params with unique name
            rebuild_collections = True
        xy_update: dict[str, float] = {}
        for param, value in params.items():
            key = param.upper()
            if key in ("X", "Y"):
                xy_update[key] = float(value)
                continue
            rec = elem._get(key)
            if rec is not None:
                rec.values[0] = str(value)
                rec.raw_line = ""
            else:
                # Try to set via parser (covers params not yet fetched)
                self._parser.set_value(elem.etype, elem.index, key, [str(value)])

        if xy_update:
            self._update_xy(elem, xy_update)

        # Rebuild collections to update _name_map if NAME was changed
        if rebuild_collections:
            self._build_collections()

    def update_elements(self, updates: dict[str, dict[str, Any]]) -> None:
        """Batch-update multiple elements.

        Parameters
        ----------
        updates:
            ``{element_name: {param: value, ...}, ...}``

        Example:
        -------
        >>> model.update_elements(
        ...     {
        ...         "L1": {"LEN": 200},
        ...         "P1": {"EFFP": 0.75},
        ...     }
        ... )
        """
        for name, params in updates.items():
            self.update_element(name, params)

    def _update_xy(self, elem: BaseElement, xy: dict[str, float]) -> None:
        """Update the XY record of an element with X and/or Y values."""
        rec = elem._get("XY")
        if rec is None:
            return
        vals = list(rec.values)
        if "X" in xy and len(vals) > 0:
            vals[0] = str(xy["X"])
        if "Y" in xy and len(vals) > 1:
            vals[1] = str(xy["Y"])
        rec.values = vals
        rec.raw_line = ""

    # ------------------------------------------------------------------
    # Add elements
    # ------------------------------------------------------------------

    def add_element(
        self,
        etype: str,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> BaseElement:
        """Add a new element instance cloned from the template (index 0).

        Parameters
        ----------
        etype:
            KDF element type keyword (e.g. ``'PIPE'``, ``'PUMP'``).
        name:
            Name for the new element (e.g. ``'L10'``, ``'P2'``).
        params:
            Optional parameter overrides applied after creation.

        Returns:
        -------
        The newly created element.
        """
        et = etype.upper()
        if et == Element.PIPE:
            raise ValueError(
                "PIPE cannot be created with add_element(); use "
                "connect_elements(..., pipe_name=...) so the pipe is created "
                "with connectivity."
            )
        return self._add_element_internal(et, name, params)

    def _add_element_internal(
        self,
        etype: str,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> BaseElement:
        """Internal element creation path used by model operations."""
        et = etype.upper()
        if et not in ELEMENT_REGISTRY:
            raise ValueError(f"Unknown element type: {etype!r}")
        name = self._ensure_unique_name(name)

        new_idx = self._parser.next_index(et)
        self._parser.clone_records(et, 0, new_idx)

        # Update NUM count
        current_count = self._parser.num_instances(et)
        self._parser.set_num_instances(et, current_count + 1)

        # Set the NAME (preserve descriptor in values[1:])
        name_rec = self._parser.get(et, new_idx, "NAME")
        if name_rec:
            name_rec.values[0] = name
            name_rec.raw_line = ""  # mark dirty for re-serialisation

        # Rebuild to pick up the new element
        self._build_collections()

        # Apply user params
        if params:
            self.update_element(name, params)

        # Auto-place if user did not explicitly provide X/Y
        x_or_y_provided = bool(params) and any(
            key.upper() in {"X", "Y"} for key in params
        )
        if not x_or_y_provided:
            from pykorf.layout import auto_place

            auto_place(self, self.get_element(name))

        return self.get_element(name)

    def _next_auto_pipe_name(self) -> str:
        """Return the next available auto-generated pipe name."""
        i = 1
        while True:
            candidate = f"L_AUTO_{i}"
            if candidate not in self._name_map:
                return candidate
            i += 1

    def add_elements(
        self,
        specs: list[tuple[str, str, dict[str, Any] | None]],
    ) -> list[BaseElement]:
        """Add multiple elements at once.

        Parameters
        ----------
        specs:
            List of ``(etype, name, params)`` tuples.  ``params`` may be
            *None* for default values.

        Returns:
        -------
        List of newly created elements.
        """
        results = []
        for spec in specs:
            etype, name = spec[0], spec[1]
            params = spec[2] if len(spec) > 2 else None
            results.append(self.add_element(etype, name, params))
        return results

    # ------------------------------------------------------------------
    # Delete elements
    # ------------------------------------------------------------------

    def delete_element(self, name: str) -> None:
        """Delete the named element from the model.

        Removes all records and decrements the NUM counter.
        """
        elem = self.get_element(name)
        et = elem.etype
        idx = elem.index

        self._parser.delete_records(et, idx)

        # Decrement NUM count
        current_count = self._parser.num_instances(et)
        if current_count > 0:
            self._parser.set_num_instances(et, current_count - 1)

        self._build_collections()

    def delete_elements(self, names: list[str]) -> None:
        """Delete multiple elements by name."""
        for name in names:
            self.delete_element(name)

    # ------------------------------------------------------------------
    # Copy elements
    # ------------------------------------------------------------------

    def copy_element(self, src_name: str, dst_name: str) -> BaseElement:
        """Copy an existing element to a new element with a different name.

        Connectivity (CON, NOZI, NOZO, NOZL) is cleared on the copy.

        Parameters
        ----------
        src_name:
            Name of the element to copy.
        dst_name:
            Name for the new copy.

        Returns:
        -------
        The newly created copy.
        """
        dst_name = self._ensure_unique_name(dst_name)
        src = self.get_element(src_name)
        et = src.etype
        new_idx = self._parser.next_index(et)

        self._parser.clone_records(et, src.index, new_idx)

        # Update NUM
        current_count = self._parser.num_instances(et)
        self._parser.set_num_instances(et, current_count + 1)

        # Set new NAME (preserve descriptor in values[1:])
        name_rec = self._parser.get(et, new_idx, "NAME")
        if name_rec:
            name_rec.values[0] = dst_name
            name_rec.raw_line = ""  # mark dirty for re-serialisation

        # Clear connectivity on the copy
        for con_param in ("CON", "NOZI", "NOZO", "NOZL", "NOZ"):
            rec = self._parser.get(et, new_idx, con_param)
            if rec is not None:
                rec.values = ["0"] * len(rec.values)
                rec.raw_line = ""

        self._build_collections()
        return self.get_element(dst_name)

    def copy_elements(
        self,
        pairs: list[tuple[str, str]],
    ) -> list[BaseElement]:
        """Copy multiple elements.

        Parameters
        ----------
        pairs:
            List of ``(src_name, dst_name)`` tuples.
        """
        return [self.copy_element(src, dst) for src, dst in pairs]

    # ------------------------------------------------------------------
    # Move elements (reorder index)
    # ------------------------------------------------------------------

    def move_element(self, name: str, target_index: int) -> None:
        """Change the index of an element within its type group.

        This swaps the element to a new index, useful for reordering.
        If *target_index* is already in use, the occupant is swapped to
        the source index.

        Parameters
        ----------
        name:
            Element NAME tag.
        target_index:
            Desired new index (must be >= 1).
        """
        elem = self.get_element(name)
        et = elem.etype
        src_idx = elem.index

        if target_index < 1:
            raise ValueError("Target index must be >= 1")
        if target_index == src_idx:
            return

        # Check if target is occupied
        target_recs = self._parser.get_all(et, target_index)
        if target_recs:
            # Swap: move target to a temp index, move source to target, move temp to source
            temp_idx = self._parser.next_index(et) + 1000
            self._parser.reindex(et, target_index, temp_idx)
            self._parser.reindex(et, src_idx, target_index)
            self._parser.reindex(et, temp_idx, src_idx)
        else:
            self._parser.reindex(et, src_idx, target_index)

        self._build_collections()

    def move_elements(self, moves: list[tuple[str, int]]) -> None:
        """Move multiple elements to new indices.

        Parameters
        ----------
        moves:
            List of ``(name, target_index)`` tuples.
        """
        for name, target in moves:
            self.move_element(name, target)

    # ------------------------------------------------------------------
    # Connectivity
    # ------------------------------------------------------------------

    def connect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str] | tuple[str, str, str]],
        name2: str | None = None,
        pipe_name: str | None = None,
    ) -> None:
        """Connect elements.

        Can be called with two names::

            model.connect_elements("L1", "P1")

        Or with a list of pairs::

            model.connect_elements([("L1", "P1"), ("L2", "P1")])

        If neither element is a pipe, a new pipe is auto-created and
        connected to both elements. You may provide ``pipe_name`` (or a
        third item in each tuple for list mode) to name the auto-created pipe.
        """
        from pykorf.connectivity import connect

        if isinstance(name1_or_pairs, list):
            for pair in name1_or_pairs:
                if len(pair) == 2:
                    n1, n2 = pair
                    p_name = None
                elif len(pair) == 3:
                    n1, n2, p_name = pair
                else:
                    raise ValueError(
                        "Each connection pair must be (name1, name2) or "
                        "(name1, name2, pipe_name)."
                    )
                self.connect_elements(n1, n2, pipe_name=p_name)
        else:
            if name2 is None:
                raise ValueError("name2 is required when name1 is a string")
            elem1 = self.get_element(name1_or_pairs)
            elem2 = self.get_element(name2)
            if elem1.etype == Element.PIPE or elem2.etype == Element.PIPE:
                if pipe_name is not None:
                    raise ValueError(
                        "pipe_name can only be provided when connecting two "
                        "non-PIPE elements."
                    )
                connect(self, name1_or_pairs, name2)
                return

            new_pipe_name = pipe_name or self._next_auto_pipe_name()
            self._add_element_internal(Element.PIPE, new_pipe_name)
            connect(self, new_pipe_name, name1_or_pairs)
            connect(self, new_pipe_name, name2)

    def disconnect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str]],
        name2: str | None = None,
    ) -> None:
        """Disconnect elements.

        Same calling convention as :meth:`connect_elements`.
        """
        from pykorf.connectivity import disconnect

        if isinstance(name1_or_pairs, list):
            for n1, n2 in name1_or_pairs:
                disconnect(self, n1, n2)
        else:
            if name2 is None:
                raise ValueError("name2 is required when name1 is a string")
            disconnect(self, name1_or_pairs, name2)

    def check_connectivity(self) -> list[str]:
        """Check all element connections for consistency.

        Returns a list of issue descriptions (empty = all OK).
        """
        from pykorf.connectivity import check_connectivity

        return check_connectivity(self)

    def get_connection(self, name: str) -> list[str]:
        """Return a list of element names connected to the named element."""
        from pykorf.connectivity import get_connections

        return get_connections(self, name)

    def get_unconnected_elements(self) -> list[str]:
        """Return a list of element names that have open connections."""
        from pykorf.connectivity import get_unconnected_elements

        return get_unconnected_elements(self)

    # ------------------------------------------------------------------
    # Layout and positioning
    # ------------------------------------------------------------------

    def check_layout(self) -> list[str]:
        """Check for element position clashes.

        Returns a list of issue descriptions (empty = no clashes).
        """
        from pykorf.layout import check_layout

        return check_layout(self)

    def visualize(self, **kwargs) -> str:
        """Create a text visualization of elements and connections.

        Returns:
        -------
        A multi-line string with element positions.
        """
        from pykorf.layout import visualize

        return visualize(self, **kwargs)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> list[str]:
        """Validate KDF format compliance.

        Returns a list of validation issues (empty = valid model).
        """
        from pykorf.validation import validate

        return validate(self)

    # ------------------------------------------------------------------
    # Convenience accessors (backward compatibility)
    # ------------------------------------------------------------------

    def pipe(self, index: int) -> Pipe:
        """Return pipe *index*, raise :exc:`ElementNotFound` if absent."""
        if index not in self.pipes:
            raise ElementNotFound(f"Pipe {index} not found in model")
        return self.pipes[index]

    def pump(self, index: int) -> Pump:
        if index not in self.pumps:
            raise ElementNotFound(f"Pump {index} not found in model")
        return self.pumps[index]

    def feed(self, index: int) -> Feed:
        if index not in self.feeds:
            raise ElementNotFound(f"Feed {index} not found in model")
        return self.feeds[index]

    def product(self, index: int) -> Product:
        if index not in self.products:
            raise ElementNotFound(f"Product {index} not found in model")
        return self.products[index]

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._parser.path

    def save(self, path: str | Path | None = None) -> None:
        """Serialise the (possibly modified) model back to a .kdf file.

        Parameters
        ----------
        path:
            Destination path.  If *None*, overwrites the source file.
        """
        self._parser.save(path)

    def save_as(self, path: str | Path) -> None:
        """Save to a new path (alias for :meth:`save` with a path argument)."""
        self._parser.save(path)

    # ------------------------------------------------------------------
    # Meta-information
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """Return a high-level dict describing the model."""
        return {
            "file": str(self._parser.path),
            "version": self.version,
            "cases": self.general.case_descriptions,
            "num_pipes": self.num_pipes,
            "num_pumps": self.num_pumps,
            "num_feeds": self._parser.num_instances("FEED"),
            "num_products": self._parser.num_instances("PROD"),
            "num_valves": self._parser.num_instances("VALVE"),
            "num_orifices": self._parser.num_instances("FO"),
            "num_exchangers": self._parser.num_instances("HX"),
        }

    def __repr__(self) -> str:
        token_to_name = {
            token: attr.lower()
            for attr, token in vars(Element).items()
            if attr.isupper() and isinstance(token, str)
        }

        parts = [f"version={self.version!r}"]
        for etype in Element.ALL:
            if etype in (Element.GEN, Element.SYMBOL, Element.TOOLS, Element.PSEUDO):
                continue
            display_name = token_to_name.get(etype, etype.lower())
            count = self._parser.num_instances(etype)
            parts.append(f"{display_name}={count}")
        parts.append(f"cases={self.num_cases}")

        return f"KorfModel({', '.join(parts)})"


# Backward compatibility alias
KorfModel = Model
