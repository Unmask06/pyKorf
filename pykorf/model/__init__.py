"""Model subpackage for KORF hydraulic model files.

This module composes the final :class:`Model` class from multiple mixins,
each providing a specific set of functionality. The composition pattern
allows for better code organization and testability.

The core functionality is provided by :class:`_ModelBase` in ``core.py``,
and the mixins add specialized capabilities:

- :class:`ElementQueryMixin`: Element querying and parameter access
- :class:`ElementCRUDMixin`: Add, update, delete, copy, move operations
- :class:`ConnectivityMixin`: Element connection management
- :class:`LayoutMixin`: Layout and visualization
- :class:`IOMixin`: File I/O and export operations
- :class:`SummaryMixin`: Model summary and validation
"""

from __future__ import annotations

from pykorf.model.connectivity import ConnectivityMixin
from pykorf.model.crud import ElementCRUDMixin
from pykorf.model.io import IOMixin
from pykorf.model.layout import LayoutMixin
from pykorf.model.query import ElementQueryMixin
from pykorf.model.summary import SummaryMixin

from .core import _ModelBase


class Model(
    ElementQueryMixin,
    ElementCRUDMixin,
    ConnectivityMixin,
    LayoutMixin,
    IOMixin,
    SummaryMixin,
    _ModelBase,
):
    """In-memory representation of a KORF .kdf hydraulic model file.

    This class is composed from multiple mixins, each providing a specific
    set of functionality:

    - ElementQueryMixin: Element querying and parameter access
    - ElementCRUDMixin: Add, update, delete, copy, move operations
    - ConnectivityMixin: Element connection management
    - LayoutMixin: Layout and visualization
    - IOMixin: File I/O and export operations
    - SummaryMixin: Model summary and validation
    """

    pass


KorfModel = Model

__all__ = ["Model", "KorfModel"]
