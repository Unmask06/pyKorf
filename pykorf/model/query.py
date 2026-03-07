"""Element querying functionality for KORF models.

This module provides the :class:`ElementQueryMixin` which adds element querying
capabilities to a model class. It assumes the following attributes/methods exist
in the class that uses this mixin:

- ``self._parser``: A KdfParser instance
- ``self._name_map``: A dict mapping element names to elements
- ``self.get_element(ename)``: Method to get an element by name
- ``self._update_xy(elem, xy_update)``: Method to update XY coordinates
- ``self._all_collections()``: Method returning all element collections
- ``self._collection_for_etype(etype)``: Method returning collection for type
"""

from __future__ import annotations

import fnmatch
from typing import TYPE_CHECKING

from pykorf.elements import BaseElement, Common
from pykorf.exceptions import ElementNotFound, ErrorContext, ParameterError
from pykorf.parser import KdfRecord

if TYPE_CHECKING:
    pass


class ElementQueryMixin:
    """Mixin providing element querying functionality.

    This mixin assumes the host class provides:
    - ``_parser``: KdfParser instance
    - ``_name_map``: Dict mapping element names to elements
    - ``get_element(ename)``: Method to get an element by name
    - ``_update_xy(elem, xy_update)``: Method to update XY coordinates
    - ``_all_collections()``: Method returning all element collections
    - ``_collection_for_etype(etype)``: Method returning collection for type
    """

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

    def get_elements(
        self,
        etype: str | None = None,
        name: str | None = None,
    ) -> list[BaseElement]:
        """Get elements with optional filtering by type and/or name.

        Parameters
        ----------
        etype:
            Filter by element type (e.g., ``'PIPE'``, ``'PUMP'``).
            If None, all element types are included.
        name:
            Filter by element name. Supports glob patterns (e.g., ``'P*'``, ``'L?'``).
            If None, all names are included.

        Returns:
        --------
        List of matching elements.

        Example:
        --------
        ```python
        # Get all pipes
        pipes = model.get_elements(etype="PIPE")

        # Get elements by name pattern
        p_elements = model.get_elements(name="P*")

        # Get pumps with names starting with "P"
        pumps = model.get_elements(etype="PUMP", name="P*")

        # Get all elements (no filters)
        all_elements = model.get_elements()
        ```
        """
        if etype is not None:
            results = self.get_elements_by_type(etype)
        else:
            results = self.elements

        if name is not None:
            results = [e for e in results if fnmatch.fnmatch(e.name, name)]

        return results

    def get_params(
        self,
        ename: str,
        param: str | None = None,
    ) -> dict[str, KdfRecord] | KdfRecord:
        """Get parameters for an element.

        Parameters
        ----------
        ename:
            Element name (NAME tag).
        param:
            Specific parameter name to retrieve. If None, returns all
            parameters as a dictionary.

        Returns:
        --------
        If ``param`` is specified, returns the single ``KdfRecord``.
        If ``param`` is None, returns a dict mapping parameter names to
        ``KdfRecord`` objects.

        Raises:
        -------
        ElementNotFound:
            If the element does not exist.
        ParameterError:
            If the specified parameter does not exist on the element.

        Example:
        --------
        ```python
        # Get all parameters as dict
        all_params = model.get_params("P1")
        # Returns: {"LEN": KdfRecord(...), "DIAM": KdfRecord(...), ...}

        # Get single parameter
        len_record = model.get_params("P1", param="LEN")
        # Returns: KdfRecord(...)

        # Access multi-case values
        values = len_record.values  # List of strings
        ```
        """
        elem = self.get_element(ename)

        if param is not None:
            record = elem._get(param.upper())
            if record is None:
                raise ParameterError(
                    f"Parameter {param!r} not found on element {ename!r}",
                    context=ErrorContext(
                        element_name=ename,
                        element_type=elem.etype,
                        parameter=param,
                    ),
                )
            return record
        else:
            all_records = self._parser.get_all(elem.etype, elem.index)
            return {rec.param: rec for rec in all_records if rec.param is not None}

    def set_params(
        self, ename: str, params: dict[str, str | int | float | list[str] | list[int] | list[float]]
    ) -> None:
        """Set parameters for an element.

        Parameters
        ----------
        ename:
            Element name (NAME tag).
        params:
            Dictionary mapping parameter names to values. Values can be:
            - Single values (int, float, str) - set as first case
            - Lists - set as multi-case values
            - Strings with semicolons - treated as multi-case

        Raises:
        -------
        ElementNotFound:
            If the element does not exist.

        Example:
        --------
        ```python
        # Set single values
        model.set_params("P1", {"LEN": 200, "DIAM": 50})

        # Set multi-case values
        model.set_params("P1", {"TFLOW": [80, 90, 60]})

        # Set from string with semicolons
        model.set_params("P1", {"TFLOW": "80;90;60"})
        ```
        """
        elem = self.get_element(ename)

        for param_name, value in params.items():
            param_key = param_name.upper()

            if param_key in (Common.X, Common.Y):
                xy_update = {param_key: float(value)}  # type: ignore[assignment]
                self._update_xy(elem, xy_update)
                continue

            if isinstance(value, (list, tuple)):
                val_list = [str(v) for v in value]
            elif isinstance(value, str) and ";" in value:
                val_list = value.split(";")
            else:
                val_list = [str(value)]

            elem.set_param(param_key, val_list)
