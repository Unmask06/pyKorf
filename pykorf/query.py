"""
Query and filter functionality for pyKorf models.

Provides a powerful query DSL for finding and filtering elements:
- Attribute-based queries
- Range queries
- Pattern matching
- Chaining and composition

Example:
    >>> from pykorf import Model
    >>> from pykorf.query import Query, attr
    >>> 
    >>> model = Model("Pumpcases.kdf")
    >>> 
    >>> # Find all pipes with diameter > 6 inches
    >>> pipes = Query(model).pipes.where(attr("diameter_inch").in_(["6", "8", "10"])).all()
    >>> 
    >>> # Find pumps with efficiency > 0.7
    >>> pumps = Query(model).pumps.where(attr("efficiency") > 0.7).all()
    >>> 
    >>> # Complex query
    >>> results = (
    ...     Query(model)
    ...     .elements
    ...     .where(attr("name").startswith("P"))
    ...     .where(attr("etype").in_(["PUMP", "PIPE"]))
    ...     .order_by("name")
    ...     .limit(10)
    ...     .all()
    ... )
"""

from __future__ import annotations

import fnmatch
import operator
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from pykorf.log import get_logger

if TYPE_CHECKING:
    from pykorf.elements.base import BaseElement
    from pykorf.model import Model

logger = get_logger(__name__)
T = TypeVar("T")


class Condition:
    """A query condition that can be evaluated against an element."""
    
    def __init__(self, func: Callable[[Any], bool], repr_str: str | None = None) -> None:
        self.func = func
        self.repr_str = repr_str or "condition"
    
    def __call__(self, obj: Any) -> bool:
        return self.func(obj)
    
    def __and__(self, other: Condition) -> Condition:
        return Condition(
            lambda obj: self(obj) and other(obj),
            f"({self.repr_str} AND {other.repr_str})"
        )
    
    def __or__(self, other: Condition) -> Condition:
        return Condition(
            lambda obj: self(obj) or other(obj),
            f"({self.repr_str} OR {other.repr_str})"
        )
    
    def __invert__(self) -> Condition:
        return Condition(
            lambda obj: not self(obj),
            f"NOT {self.repr_str}"
        )
    
    def __repr__(self) -> str:
        return self.repr_str


class Attribute:
    """Represents an attribute for querying."""
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    def _get_value(self, obj: Any) -> Any:
        """Get attribute value from object."""
        if hasattr(obj, self.name):
            return getattr(obj, self.name)
        if isinstance(obj, dict):
            return obj.get(self.name)
        # Try to get from element properties
        if hasattr(obj, "_get"):
            rec = obj._get(self.name.upper())
            if rec and rec.values:
                return rec.values[0]
        return None
    
    def __eq__(self, value: Any) -> Condition:  # type: ignore[override]
        return Condition(
            lambda obj: self._get_value(obj) == value,
            f"{self.name} == {value!r}"
        )
    
    def __ne__(self, value: Any) -> Condition:  # type: ignore[override]
        return Condition(
            lambda obj: self._get_value(obj) != value,
            f"{self.name} != {value!r}"
        )
    
    def __lt__(self, value: Any) -> Condition:
        return Condition(
            lambda obj: self._get_value(obj) < value,
            f"{self.name} < {value!r}"
        )
    
    def __le__(self, value: Any) -> Condition:
        return Condition(
            lambda obj: self._get_value(obj) <= value,
            f"{self.name} <= {value!r}"
        )
    
    def __gt__(self, value: Any) -> Condition:
        return Condition(
            lambda obj: self._get_value(obj) > value,
            f"{self.name} > {value!r}"
        )
    
    def __ge__(self, value: Any) -> Condition:
        return Condition(
            lambda obj: self._get_value(obj) >= value,
            f"{self.name} >= {value!r}"
        )
    
    def in_(self, values: list[Any]) -> Condition:
        """Check if attribute is in a list of values."""
        return Condition(
            lambda obj: self._get_value(obj) in values,
            f"{self.name} in {values!r}"
        )
    
    def contains(self, substring: str) -> Condition:
        """Check if string attribute contains substring."""
        return Condition(
            lambda obj: substring in str(self._get_value(obj) or ""),
            f"{self.name} contains {substring!r}"
        )
    
    def startswith(self, prefix: str) -> Condition:
        """Check if string attribute starts with prefix."""
        return Condition(
            lambda obj: str(self._get_value(obj) or "").startswith(prefix),
            f"{self.name} startswith {prefix!r}"
        )
    
    def endswith(self, suffix: str) -> Condition:
        """Check if string attribute ends with suffix."""
        return Condition(
            lambda obj: str(self._get_value(obj) or "").endswith(suffix),
            f"{self.name} endswith {suffix!r}"
        )
    
    def matches(self, pattern: str) -> Condition:
        """Check if attribute matches glob pattern."""
        return Condition(
            lambda obj: fnmatch.fnmatch(str(self._get_value(obj) or ""), pattern),
            f"{self.name} matches {pattern!r}"
        )
    
    def regex(self, pattern: str) -> Condition:
        """Check if attribute matches regex pattern."""
        regex = re.compile(pattern)
        return Condition(
            lambda obj: bool(regex.search(str(self._get_value(obj) or ""))),
            f"{self.name} regex {pattern!r}"
        )
    
    def between(self, low: Any, high: Any) -> Condition:
        """Check if attribute is between two values."""
        return Condition(
            lambda obj: low <= self._get_value(obj) <= high,
            f"{self.name} between ({low!r}, {high!r})"
        )
    
    def is_none(self) -> Condition:
        """Check if attribute is None."""
        return Condition(
            lambda obj: self._get_value(obj) is None,
            f"{self.name} is None"
        )
    
    def is_not_none(self) -> Condition:
        """Check if attribute is not None."""
        return Condition(
            lambda obj: self._get_value(obj) is not None,
            f"{self.name} is not None"
        )


def attr(name: str) -> Attribute:
    """Create an attribute selector for queries.
    
    Example:
        >>> query.where(attr("name").startswith("P"))
        >>> query.where(attr("length_m") > 100)
    """
    return Attribute(name)


@dataclass
class QueryResult(Generic[T]):
    """Result of a query with chainable methods."""
    
    items: list[T]
    
    def __iter__(self):
        return iter(self.items)
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __getitem__(self, index: int) -> T:
        return self.items[index]
    
    def first(self) -> T | None:
        """Return first item or None if empty."""
        return self.items[0] if self.items else None
    
    def last(self) -> T | None:
        """Return last item or None if empty."""
        return self.items[-1] if self.items else None
    
    def count(self) -> int:
        """Return count of items."""
        return len(self.items)
    
    def pluck(self, attr_name: str) -> list[Any]:
        """Extract a single attribute from all items."""
        return [getattr(item, attr_name, None) for item in self.items]
    
    def group_by(self, attr_name: str) -> dict[Any, list[T]]:
        """Group items by an attribute."""
        result: dict[Any, list[T]] = {}
        for item in self.items:
            key = getattr(item, attr_name, None)
            result.setdefault(key, []).append(item)
        return result
    
    def map(self, func: Callable[[T], Any]) -> list[Any]:
        """Apply a function to each item."""
        return [func(item) for item in self.items]


class ElementQuery:
    """Query builder for model elements."""
    
    def __init__(self, model: Model, elements: list[BaseElement] | None = None) -> None:
        self.model = model
        self._elements = elements or []
        self._conditions: list[Condition] = []
        self._order_by: str | None = None
        self._reverse: bool = False
        self._limit: int | None = None
    
    def where(self, condition: Condition) -> ElementQuery:
        """Add a filter condition."""
        new_query = ElementQuery(self.model, self._elements[:])
        new_query._conditions = self._conditions + [condition]
        new_query._order_by = self._order_by
        new_query._reverse = self._reverse
        new_query._limit = self._limit
        return new_query
    
    def order_by(self, attr_name: str, reverse: bool = False) -> ElementQuery:
        """Set ordering."""
        new_query = ElementQuery(self.model, self._elements[:])
        new_query._conditions = self._conditions[:]
        new_query._order_by = attr_name
        new_query._reverse = reverse
        new_query._limit = self._limit
        return new_query
    
    def limit(self, n: int) -> ElementQuery:
        """Limit number of results."""
        new_query = ElementQuery(self.model, self._elements[:])
        new_query._conditions = self._conditions[:]
        new_query._order_by = self._order_by
        new_query._reverse = self._reverse
        new_query._limit = n
        return new_query
    
    def all(self) -> QueryResult[BaseElement]:
        """Execute query and return all matching elements."""
        results = self._elements
        
        # Apply conditions
        for condition in self._conditions:
            results = [e for e in results if condition(e)]
        
        # Apply ordering
        if self._order_by:
            results = sorted(
                results,
                key=lambda e: getattr(e, self._order_by, 0) or 0,
                reverse=self._reverse
            )
        
        # Apply limit
        if self._limit is not None:
            results = results[:self._limit]
        
        return QueryResult(results)
    
    def one(self) -> BaseElement:
        """Execute query and return exactly one element.
        
        Raises:
            ValueError: If zero or more than one element matches.
        """
        results = self.all()
        if len(results) == 0:
            raise ValueError("Query returned no results")
        if len(results) > 1:
            raise ValueError(f"Query returned {len(results)} results, expected 1")
        return results[0]
    
    def exists(self) -> bool:
        """Check if any element matches the query."""
        return len(self.all()) > 0


class Query:
    """Main query interface for models."""
    
    def __init__(self, model: Model) -> None:
        self.model = model
    
    @property
    def elements(self) -> ElementQuery:
        """Query all elements."""
        return ElementQuery(self.model, self.model.elements)
    
    @property
    def pipes(self) -> ElementQuery:
        """Query pipes."""
        return ElementQuery(
            self.model,
            [e for e in self.model.pipes.values() if e.index > 0]
        )
    
    @property
    def pumps(self) -> ElementQuery:
        """Query pumps."""
        return ElementQuery(
            self.model,
            [e for e in self.model.pumps.values() if e.index > 0]
        )
    
    @property
    def valves(self) -> ElementQuery:
        """Query valves."""
        return ElementQuery(
            self.model,
            [e for e in self.model.valves.values() if e.index > 0]
        )
    
    @property
    def feeds(self) -> ElementQuery:
        """Query feeds."""
        return ElementQuery(
            self.model,
            [e for e in self.model.feeds.values() if e.index > 0]
        )
    
    @property
    def products(self) -> ElementQuery:
        """Query products."""
        return ElementQuery(
            self.model,
            [e for e in self.model.products.values() if e.index > 0]
        )
    
    @property
    def vessels(self) -> ElementQuery:
        """Query vessels."""
        return ElementQuery(
            self.model,
            [e for e in self.model.vessels.values() if e.index > 0]
        )
    
    def by_type(self, etype: str) -> ElementQuery:
        """Query elements by type."""
        return ElementQuery(
            self.model,
            self.model.get_elements_by_type(etype)
        )
    
    def by_name(self, pattern: str) -> ElementQuery:
        """Query elements by name pattern (glob)."""
        return ElementQuery(
            self.model,
            [e for e in self.model.elements if fnmatch.fnmatch(e.name, pattern)]
        )
    
    def connected_to(self, name: str) -> ElementQuery:
        """Query elements connected to a given element."""
        from pykorf.connectivity import get_connections
        try:
            conn_names = get_connections(self.model, name)
            return ElementQuery(
                self.model,
                [self.model.get_element(n) for n in conn_names]
            )
        except Exception:
            return ElementQuery(self.model, [])


def find(
    model: Model,
    **kwargs: Any,
) -> QueryResult[BaseElement]:
    """Simple finder function for quick searches.
    
    Example:
        >>> find(model, etype="PUMP", name="P1")
        >>> find(model, etype="PIPE", diameter_inch="6")
    """
    results = []
    
    for elem in model.elements:
        match = True
        for key, value in kwargs.items():
            if key == "etype":
                if elem.etype != value:
                    match = False
                    break
            elif hasattr(elem, key):
                if getattr(elem, key) != value:
                    match = False
                    break
            else:
                match = False
                break
        
        if match:
            results.append(elem)
    
    return QueryResult(results)


__all__ = [
    "Query",
    "ElementQuery",
    "QueryResult",
    "Condition",
    "Attribute",
    "attr",
    "find",
]
