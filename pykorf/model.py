"""KorfModel – top-level container for a KORF .kdf file.

All element collections (pipes, pumps, feeds …) are lazily constructed
from the :class:`KdfParser` record list and exposed as integer-indexed
dicts.  Index 0 is the default template; real instances start at 1.

Basic workflow::

    from pykorf import KorfModel

    model = KorfModel.load("Pumpcases.kdf")

    # Inspect
    print(model.general.case_descriptions)  # ['NORMAL', 'RATED', 'MINIMUM']
    print(model.pipes[1].get_flow())  # ['50', '55', '20']
    print(model.pumps[1].head_m)  # 155.6

    # Edit
    model.pipes[1].set_flow([60, 65, 25])
    model.pumps[1].set_efficiency(0.72)

    # Save
    model.save("Pumpcases_new.kdf")
"""

from __future__ import annotations

from pathlib import Path

from pykorf.elements import (
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


class KorfModel:
    """In-memory representation of a KORF .kdf hydraulic model file.

    Parameters
    ----------
    parser:
        A loaded :class:`KdfParser` instance.

    Instantiation
    -------------
    Use :meth:`load` rather than calling the constructor directly::

        model = KorfModel.load("path/to/model.kdf")
    """

    def __init__(self, parser: KdfParser):
        self._parser = parser
        self._build_collections()

    # ------------------------------------------------------------------
    # Class constructors
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> KorfModel:
        """Load a .kdf file and return a :class:`KorfModel`."""
        p = KdfParser(path)
        p.load()
        return cls(p)

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
    # Convenience accessors
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
        return (
            f"KorfModel(version={self.version!r}, "
            f"pipes={self.num_pipes}, pumps={self.num_pumps}, "
            f"cases={self.num_cases})"
        )
