"""Connectivity facade for KORF models.

This module provides the :class:`ConnectivityMixin` which adds connectivity
management capabilities to a model class. It delegates to the
:mod:`pykorf.connectivity` module for the actual connection logic.

This mixin assumes the host class provides:

- ``self.get_element(name)``: Method to get an element by name
- ``self._add_element_internal(etype, name, ...)``: Method to add elements
- ``self._position_pipe_between(pipe_name, name1, name2)``: Method to position pipes
- ``self._next_auto_pipe_name()``: Method to generate auto pipe names
- ``self._name_map``: Dict mapping element names to elements
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.elements import Element

if TYPE_CHECKING:
    pass


class ConnectivityMixin:
    """Mixin providing connectivity management functionality.

    This mixin assumes the host class provides:
    - ``get_element(name)``: Method to get an element by name
    - ``_add_element_internal(etype, name, ...)``: Method to add elements
    - ``_position_pipe_between(pipe_name, name1, name2)``: Method to position pipes
    - ``_next_auto_pipe_name()``: Method to generate auto pipe names
    - ``_name_map``: Dict mapping element names to elements
    """

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
                        "Each connection pair must be (name1, name2) or (name1, name2, pipe_name)."
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
                        "pipe_name can only be provided when connecting two non-PIPE elements."
                    )
                connect(self, name1_or_pairs, name2)
                return

            new_pipe_name = pipe_name or self._next_auto_pipe_name()
            self._add_element_internal(Element.PIPE, new_pipe_name, auto_position=False)
            self._position_pipe_between(new_pipe_name, name1_or_pairs, name2)
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
