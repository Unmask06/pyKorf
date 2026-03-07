"""SummaryMixin – validation, convenience accessors, and summary methods.

This mixin is designed to be used with the Model class and assumes the following
attributes are available on `self`:

    - `self._parser` – KdfParser instance
    - `self.version` – property returning model version
    - `self.general` – General element instance
    - `self.num_cases` – property returning number of cases
    - `self.pipes` – dict of Pipe elements
    - `self.pumps` – dict of Pump elements
    - `self.feeds` – dict of Feed elements
    - `self.products` – dict of Product elements
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.elements import Element, Feed, General, Pipe, Product, Pump
from pykorf.exceptions import ElementNotFound
from pykorf.parser import KdfParser

if TYPE_CHECKING:
    pass


class SummaryMixin:
    """Mixin providing validation, convenience accessors, and summary methods."""

    _parser: "KdfParser"
    version: str
    general: "General"
    num_cases: int
    num_pipes: int
    num_pumps: int
    pipes: dict[int, Pipe]
    pumps: dict[int, Pump]
    feeds: dict[int, Feed]
    products: dict[int, Product]

    def validate(self) -> list[str]:
        """Validate KDF format compliance.

        Returns a list of validation issues (empty = valid model).
        """
        from pykorf.validation import validate

        return validate(self)  # type: ignore[arg-type]

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
