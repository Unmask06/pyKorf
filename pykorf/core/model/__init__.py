"""Services package for KORF model operations.

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

from typing import TYPE_CHECKING, Any

from pykorf.core.model.connectivity import ConnectivityService
from pykorf.core.model.core import _ModelBase
from pykorf.core.model.element import ElementService
from pykorf.core.model.io import IOService
from pykorf.core.model.layout import LayoutService
from pykorf.core.model.query import QueryService
from pykorf.core.model.summary import SummaryService

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "ConnectivityService",
    "ElementService",
    "IOService",
    "LayoutService",
    "Model",
    "QueryService",
    "SummaryService",
]


class Model(_ModelBase):
    """Full Model class with all service mixins.

    This is the main entry point for working with KORF models.
    """

    def __init__(self, path: str | Path | None = None):
        super().__init__(path)
        # Initialize service instances bound to this model
        self._element_service = ElementService(self)
        self._query_service = QueryService(self)
        self._connectivity_service = ConnectivityService(self)
        self._layout_service = LayoutService(self)
        self._io_service = IOService(self)
        self._summary_service = SummaryService(self)

    # Element operations (delegate to _element_service)
    def add_element(self, etype: str, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._element_service.add_element(etype, name, params)

    def add_elements(self, elements: list[tuple[str, str, dict[str, Any]]]) -> None:
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

    # Query operations (delegate to _query_service)
    def get_element(self, name: str, etype: str | None = None) -> Any:
        return self._query_service.get_element(name, etype)

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

    # Connectivity operations (delegate to _connectivity_service)
    def connect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str] | tuple[str, str, str]],
        name2: str | None = None,
        pipe_name: str | None = None,
    ) -> None:
        return self._connectivity_service.connect_elements(name1_or_pairs, name2, pipe_name)

    def disconnect_elements(self, element1: str, element2: str) -> None:
        return self._connectivity_service.disconnect_elements(element1, element2)

    # Layout operations (delegate to _layout_service)
    def auto_place(self, element: Any) -> None:
        return self._layout_service.auto_place(element)

    def check_layout(self) -> list[str]:
        return self._layout_service.check_layout()

    # I/O operations (delegate to _io_service)
    def save(self, path: str | Path | None = None) -> None:
        return self._io_service.save(path)

    def save_as(self, path: str | Path, *, check_layout: bool = True, overwrite: bool = False) -> None:
        return self._io_service.save_as(path, check_layout=check_layout, overwrite=overwrite)

    def to_excel(self, path: str | Path) -> str:
        return self._io_service.to_excel(path)

    def to_dataframes(self) -> dict[str, Any]:
        return self._io_service.to_dataframes()

    def from_excel(self, path: str | Path) -> None:
        return self._io_service.from_excel(path)

    def from_dataframes(self, data: dict[str, Any]) -> None:
        return self._io_service.from_dataframes(data)

    # Summary operations (delegate to _summary_service)
    def get_summary(self) -> dict[str, Any]:
        return self._summary_service.summary()

    def validate(self) -> list[str]:
        return self._summary_service.validate()

    def __repr__(self) -> str:
        return self._summary_service.__repr__()

    # Internal methods (for advanced usage)
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
