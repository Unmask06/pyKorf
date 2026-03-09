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
        model.elements.add_element("PUMP", "P1", {"EFFP": 0.75})

        # Query operations
        pipes = model.query.get_elements(etype="PIPE", name="L*")

        # Connectivity operations
        model.connectivity.connect_elements("L1", "P1")

        # Layout operations
        model.layout.auto_place(element)

        # I/O operations
        model.io.save()
        model.io.to_excel("export.xlsx")

        # Summary operations
        stats = model.summary.get_summary()
"""

from __future__ import annotations

from pykorf.model.services.connectivity import ConnectivityService
from pykorf.model.services.element import ElementService
from pykorf.model.services.io import IOService
from pykorf.model.services.layout import LayoutService
from pykorf.model.services.query import QueryService
from pykorf.model.services.summary import SummaryService

__all__ = [
    "ConnectivityService",
    "ElementService",
    "IOService",
    "LayoutService",
    "QueryService",
    "SummaryService",
]
