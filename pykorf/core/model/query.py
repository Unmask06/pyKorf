"""Query service for KORF model element operations.

This module provides the :class:`QueryService` which encapsulates element querying
capabilities for a KORF model. It delegates model-specific operations to the
associated Model instance.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pykorf.core.elements import BaseElement, Common
from pykorf.core.exceptions import ErrorContext, ParameterError
from pykorf.core.parser import KdfRecord

if TYPE_CHECKING:
    from pykorf.core.model import Model


@dataclass(frozen=True, slots=True)
class QueryService:
    """Service for querying elements and their parameters in a KORF model.

    This service provides methods to retrieve elements by type, name patterns,
    and to get/set element parameters. It operates on the associated Model
    instance and delegates model-level operations to it.

    Args:
        model: The Model instance to query.
    """

    model: Model

    @property
    def elements(self) -> list[BaseElement]:
        """Return all real element instances (index >= 1) across all types."""
        result: list[BaseElement] = []
        for collection in self.model._all_collections():
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

        Returns:
            List of elements matching the specified type.
        """
        collection = self.model._collection_for_etype(etype)
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
            List of matching elements.

        Example:
            ```python
            # Get all pipes
            pipes = query_service.get_elements(etype="PIPE")

            # Get elements by name pattern
            p_elements = query_service.get_elements(name="P*")

            # Get pumps with names starting with "P"
            pumps = query_service.get_elements(etype="PUMP", name="P*")

            # Get all elements (no filters)
            all_elements = query_service.get_elements()
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
            If ``param`` is specified, returns the single ``KdfRecord``.
            If ``param`` is None, returns a dict mapping parameter names to
            ``KdfRecord`` objects.

        Raises:
            ElementNotFound:
                If the element does not exist.
            ParameterError:
                If the specified parameter does not exist on the element.

        Example:
            ```python
            # Get all parameters as dict
            all_params = query_service.get_params("P1")
            # Returns: {"LEN": KdfRecord(...), "DIAM": KdfRecord(...), ...}

            # Get single parameter
            len_record = query_service.get_params("P1", param="LEN")
            # Returns: KdfRecord(...)

            # Access multi-case values
            values = len_record.values  # List of strings
            ```
        """
        elem = self.model.get_element(ename)

        if param is not None:
            record = elem.get_param(param.upper())
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
            all_records = self.model._parser.get_all(elem.etype, elem.index)
            return {rec.param: rec for rec in all_records if rec.param is not None}

    def set_params(
        self,
        ename: str,
        params: dict[str, str | int | float | list[str] | list[int] | list[float]],
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
            ElementNotFound:
                If the element does not exist.

        Example:
            ```python
            # Set single values
            query_service.set_params("P1", {"LEN": 200, "DIAM": 50})

            # Set multi-case values
            query_service.set_params("P1", {"TFLOW": [80, 90, 60]})

            # Set from string with semicolons
            query_service.set_params("P1", {"TFLOW": "80;90;60"})
            ```
        """
        elem = self.model.get_element(ename)

        for param_name, value in params.items():
            param_key = param_name.upper()

            if param_key in (Common.X, Common.Y):
                # Get current position and update the specific coordinate
                xy_rec = elem.get_param(Common.XY)
                if xy_rec and len(xy_rec.values) >= 2:
                    if param_key == Common.X:
                        xy_rec.values[0] = str(value)
                    else:
                        xy_rec.values[1] = str(value)
                    xy_rec.raw_line = ""
                continue

            if isinstance(value, (list, tuple)):
                val_list = [str(v) for v in value]
            elif isinstance(value, str) and ";" in value:
                val_list = value.split(";")
            else:
                val_list = [str(value)]

            elem.set_param(param_key, val_list)


    def get_element(self, name: str, etype: str | None = None) -> BaseElement:
        """Get a single element by name.

        Parameters
        ----------
        name:
            Element name to find.
        etype:
            Optional element type to narrow the search.

        Returns
        -------
        BaseElement
            The element matching the name (and type if specified).

        Raises
        ------
        ElementNotFound
            If no element with the given name exists.
        """
        from pykorf.core.exceptions import ElementNotFound

        # Get all elements matching the name
        candidates = self.get_elements(etype=etype, name=name)
        
        if not candidates:
            available = [e.name for e in self.elements]
            raise ElementNotFound(name, available_names=available)
        
        # Return first match
        return candidates[0]
