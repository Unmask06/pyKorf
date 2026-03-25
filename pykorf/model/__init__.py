"""Model subpackage for KORF hydraulic model files.

This module provides the :class:`Model` class which serves as the primary
interface for working with KORF hydraulic model files. The Model class uses
a service-based architecture where specialized functionality is delegated to
service classes, providing better code organization, testability, and separation
of concerns.

The core functionality is provided by :class:`_ModelBase` in ``core.py``,
and the following services handle specific domains:

- :class:`ElementService`: Element CRUD operations (add, update, delete, copy, move)
- :class:`QueryService`: Element querying and parameter access
- :class:`ConnectivityService`: Element connection management
- :class:`LayoutService`: Layout and visualization
- :class:`IOService`: File I/O and export operations
- :class:`SummaryService`: Model summary and validation

Example:
    ```python
    from pykorf import Model

    # Load a model
    model = Model("example.kdf")

    # Query elements
    pipes = model.get_elements(etype="PIPE")

    # Update elements
    model.update_element("L1", {"LEN": 200})

    # Manage connectivity
    model.connect_elements("P1", "L1")

    # Save changes
    model.save()
    ```
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pykorf.elements import BaseElement, Feed, Pipe, Product, Pump
from pykorf.model.services import (
    ConnectivityService,
    ElementService,
    IOService,
    LayoutService,
    QueryService,
    SummaryService,
)
from pykorf.parser import KdfRecord

from .core import _ModelBase


class Model(_ModelBase):
    """In-memory representation of a KORF .kdf hydraulic model file.

    This class provides a high-level interface for loading, modifying, and
    saving KORF hydraulic models. It delegates specialized operations to
    service classes while presenting a unified API.

    The service-based architecture separates concerns:
    - ElementService: CRUD operations for elements
    - QueryService: Element querying and parameter access
    - ConnectivityService: Managing connections between elements
    - LayoutService: Element positioning and visualization
    - IOService: File I/O and export operations
    - SummaryService: Model summary and validation

    Example:
        ```python
        # Load a model
        model = Model("cooling_circuit.kdf")

        # Get element counts
        print(f"Pipes: {model.num_pipes}, Pumps: {model.num_pumps}")

        # Query and modify elements
        for pipe in model.get_elements(etype="PIPE"):
            print(f"{pipe.name}: {pipe.diameter}")

        model.update_element("L1", {"LEN": 300})

        # Connect elements
        model.connect_elements("P1", "L1")

        # Save changes
        model.save()
        ```
    """

    def __init__(self, path: str | Path | None = None):
        super().__init__(path)

        # Compose services
        self._element_service = ElementService(model=self)
        self._query_service = QueryService(model=self)
        self._connectivity_service = ConnectivityService(model=self)
        self._layout_service = LayoutService(model=self)
        self._io_service = IOService(model=self)
        self._summary_service = SummaryService(model=self)

    # Service properties
    @property
    def elements_service(self) -> ElementService:
        """Access the ElementService for CRUD operations."""
        return self._element_service

    @property
    def query(self) -> QueryService:
        """Access the QueryService for filtering and parameter access."""
        return self._query_service

    @property
    def connectivity(self) -> ConnectivityService:
        """Access the ConnectivityService for managing element connections."""
        return self._connectivity_service

    @property
    def layout(self) -> LayoutService:
        """Access the LayoutService for positioning and visualization."""
        return self._layout_service

    @property
    def io(self) -> IOService:
        """Access the IOService for file I/O and export operations."""
        return self._io_service

    @property
    def summary_service(self) -> SummaryService:
        """Access the SummaryService for validation and statistics."""
        return self._summary_service

    # ELEMENT CRUD - delegate to ElementService
    def update_element(self, name: str, params: dict[str, Any]) -> None:
        """Update parameters of the named element.

        Args:
            name: Element NAME tag (e.g., ``'L1'``, ``'P1'``).
            params: Dict of ``{KDF_PARAM: value}``. Values are set as the first
                token of the record's value list. Special keys ``'X'`` and
                ``'Y'`` update the XY record.

        Example:
            ```python
            model.update_element("L1", {"LEN": 200, "TFLOW": "80;90;60"})
            ```
        """
        return self._element_service.update_element(name, params)

    def update_elements(self, updates: dict[str, dict[str, Any]]) -> None:
        """Batch-update multiple elements.

        Args:
            updates: ``{element_name: {param: value, ...}, ...}``

        Example:
            ```python
            model.update_elements(
                {
                    "L1": {"LEN": 200},
                    "P1": {"EFFP": 0.75},
                }
            )
            ```
        """
        return self._element_service.update_elements(updates)

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
            KDF element type keyword (e.g., ``'PIPE'``, ``'PUMP'``).
        name:
            Name for the new element (e.g., ``'L10'``, ``'P2'``).
        params:
            Optional parameter overrides applied after creation.

        Returns:
            The newly created element.
        """
        return self._element_service.add_element(etype, name, params)

    def add_elements(
        self,
        specs: list[tuple[str, str, dict[str, Any] | None]],
    ) -> list[BaseElement]:
        """Add multiple elements at once.

        Parameters
        ----------
        specs:
            List of ``(etype, name, params)`` tuples. ``params`` may be
            *None* for default values.

        Returns:
            List of newly created elements.
        """
        return self._element_service.add_elements(specs)

    def delete_element(self, name: str) -> None:
        """Delete the named element from the model.

        Removes all records and reindexes remaining elements to be continuous.
        """
        return self._element_service.delete_element(name)

    def delete_elements(self, names: list[str]) -> None:
        """Delete multiple elements by name."""
        return self._element_service.delete_elements(names)

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
            The newly created copy.
        """
        return self._element_service.copy_element(src_name, dst_name)

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
        return self._element_service.copy_elements(pairs)

    def move_element(self, name: str, target_index: int) -> None:
        """Change the index of an element within its type group.

        This moves the element to a new index, useful for reordering.
        If *target_index* is already in use, the occupant is swapped to
        the source index.

        Parameters
        ----------
        name:
            Element NAME tag.
        target_index:
            Desired new index (must be >= 1).
        """
        return self._element_service.move_element(name, target_index)

    def move_elements(self, moves: list[tuple[str, int]]) -> None:
        """Move multiple elements to new indices.

        Parameters
        ----------
        moves:
            List of ``(name, target_index)`` tuples.
        """
        return self._element_service.move_elements(moves)

    # Internal methods used by other services
    def _add_element_internal(
        self,
        etype: str,
        name: str,
        params: dict[str, Any] | None = None,
        *,
        auto_position: bool = True,
    ) -> BaseElement:
        """Internal element creation path used by model operations."""
        return self._element_service._add_element_internal(
            etype, name, params, auto_position=auto_position
        )

    def _next_auto_pipe_name(self) -> str:
        """Return the next available auto-generated pipe name."""
        return self._element_service._next_auto_pipe_name()

    def _position_pipe_between(self, pipe_name: str, elem1_name: str, elem2_name: str) -> None:
        """Position a pipe between two elements with proper spacing."""
        return self._element_service._position_pipe_between(pipe_name, elem1_name, elem2_name)

    def reindex_element(self, etype: str, old_index: int, new_index: int) -> None:
        """Update the index of an element and all its external references.

        This is a low-level operation. Use with caution.
        """
        return self._element_service.reindex_element(etype, old_index, new_index)

    def compact_indices(self, etype: str | None = None) -> None:
        """Reorder element indices to be continuous (1..N) and update NUM.

        If *etype* is None, compacts all element types.
        """
        return self._element_service.compact_indices(etype)

    # QUERY - delegate to QueryService
    @property
    def elements(self) -> list[BaseElement]:
        """Return all real element instances (index >= 1) across all types."""
        return self._query_service.elements

    def get_elements_by_type(self, etype: str) -> list[BaseElement]:
        """Return all instances of a given element type (index >= 1).

        Parameters
        ----------
        etype:
            KDF element type keyword, e.g., ``'PIPE'``, ``'PUMP'``, ``'FO'``.
        """
        return self._query_service.get_elements_by_type(etype)

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
            pipes = model.get_elements(etype="PIPE")

            # Get elements by name pattern
            p_elements = model.get_elements(name="P*")

            # Get pumps with names starting with "P"
            pumps = model.get_elements(etype="PUMP", name="P*")

            # Get all elements (no filters)
            all_elements = model.get_elements()
            ```
        """
        return self._query_service.get_elements(etype, name)

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

        Example:
            ```python
            # Get all parameters as dict
            all_params = model.get_params("P1")

            # Get single parameter
            len_record = model.get_params("P1", param="LEN")
            ```
        """
        return self._query_service.get_params(ename, param)

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

        Example:
            ```python
            # Set single values
            model.set_params("P1", {"LEN": 200, "DIAM": 50})

            # Set multi-case values
            model.set_params("P1", {"TFLOW": [80, 90, 60]})

            # Set from string with semicolons
            model.set_params("P1", {"TFLOW": "80;90;60"})
            ```
        """
        return self._query_service.set_params(ename, params)

    # CONNECTIVITY - delegate to ConnectivityService
    def connect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str] | tuple[str, str, str]],
        name2: str | None = None,
        pipe_name: str | None = None,
    ) -> None:
        """Connect elements together.

        When connecting two non-PIPE elements, a new PIPE is automatically
        created between them.

        Parameters
        ----------
        name1_or_pairs:
            Either a single element name or a list of connection tuples.
            Each tuple can be (name1, name2) or (name1, name2, pipe_name).
        name2:
            Second element name (required when name1 is a string).
        pipe_name:
            Optional name for auto-created pipe (only when connecting
            two non-PIPE elements).
        """
        return self._connectivity_service.connect_elements(name1_or_pairs, name2, pipe_name)

    def disconnect_elements(
        self,
        name1_or_pairs: str | list[tuple[str, str]],
        name2: str | None = None,
    ) -> None:
        """Disconnect elements from each other.

        Parameters
        ----------
        name1_or_pairs:
            Either a single element name or a list of (name1, name2) tuples.
        name2:
            Second element name (required when name1 is a string).
        """
        return self._connectivity_service.disconnect_elements(name1_or_pairs, name2)

    def check_connectivity(self) -> list[str]:
        """Check all element connections for consistency.

        Returns:
            List of connectivity issues (empty if all connections are valid).
        """
        return self._connectivity_service.check_connectivity()

    def get_connection(self, name: str) -> list[str]:
        """Return a list of element names connected to the named element."""
        return self._connectivity_service.get_connections(name)

    def get_unconnected_elements(self) -> list[str]:
        """Return a list of element names that have open connections."""
        return self._connectivity_service.get_unconnected_elements()

    # LAYOUT - delegate to LayoutService
    def check_layout(self) -> list[str]:
        """Check for element position clashes and layout issues.

        Returns:
            List of layout issues (empty if layout is valid).
        """
        return self._layout_service.check_layout()

    def get_position(self, elem: BaseElement) -> tuple[float, float] | None:
        """Extract the primary (x, y) position from an element's XY record.

        Args:
            elem: The element to get the position for.

        Returns:
            (x, y) tuple or None if not placed.
        """
        return self._layout_service.get_position(elem)

    def set_position(
        self,
        name_or_elem: str | BaseElement,
        x: float,
        y: float,
    ) -> None:
        """Set the primary (x, y) position of an element.

        Args:
            name_or_elem: Element name or object.
            x: X coordinate.
            y: Y coordinate.
        """
        return self._layout_service.set_position(name_or_elem, x, y)

    def auto_place(self, elem: BaseElement) -> None:
        """Automatically position a single element.

        Args:
            elem: The element to position.
        """
        return self._layout_service.auto_place(elem)

    def auto_layout(
        self,
        spacing: float | None = None,
        strategy: str = "grid",
        route_pipes: bool = False,
    ) -> None:
        """Automatically arrange all unplaced elements.

        Parameters
        ----------
        spacing:
            Spacing between elements. If None, uses default comfort spacing.
        strategy:
            ``"grid"`` (default) - simple rectangular grid.
            ``"flow"`` - topological left-to-right placement ordered by
            element connectivity (FEED -> equipment -> PROD).
        route_pipes:
            When True, route every pipe as an orthogonal polyline after
            placement. Combines layout + routing in one call. Default False.
        """
        return self._layout_service.auto_layout(spacing, strategy, route_pipes)

    def route_pipe(self, pipe: BaseElement, bend: str = "auto") -> None:
        """Route a single pipe as an orthogonal polyline between its endpoints.

        Parameters
        ----------
        pipe:
            A PIPE element.
        bend:
            Corner direction: ``"h"`` horizontal-first, ``"v"`` vertical-first,
            ``"auto"`` (default) chosen by dominant displacement.
        """
        return self._layout_service.route_pipe(pipe, bend)

    def route_all_pipes(self, bend: str = "auto") -> None:
        """Route every pipe with two connected elements as an orthogonal polyline.

        Parameters
        ----------
        bend:
            Corner direction applied to all pipes.
            ``"h"``, ``"v"``, or ``"auto"`` (default).
        """
        return self._layout_service.route_all_pipes(bend)

    def get_polyline(self, pipe: BaseElement) -> list[tuple[float, float]]:
        """Get the drawn waypoints from a pipe's XY record.

        Parameters
        ----------
        pipe:
            A PIPE element.

        Returns:
        -------
        list[tuple[float, float]]
            Ordered list of (x, y) waypoint tuples.  Empty if none are set.
        """
        return self._layout_service.get_polyline(pipe)

    def set_polyline(self, pipe: BaseElement, points: list[tuple[float, float]]) -> None:
        """Write waypoints into a pipe's XY record.

        Parameters
        ----------
        pipe:
            A PIPE element.
        points:
            Ordered list of (x, y) waypoints.
        """
        return self._layout_service.set_polyline(pipe, points)

    def add_bend(
        self,
        pipe: BaseElement,
        x: float,
        y: float,
        index: int | None = None,
    ) -> None:
        """Insert a bend waypoint into a pipe's polyline.

        Creates an angular corner in the pipe drawing.  The most common
        use-case is making an L-shaped route::

            start ──► corner ──► end

        For an orthogonal L from ``(x1, y1)`` to ``(x2, y2)``:

        - horizontal-first: ``add_bend(pipe, x2, y1)``
        - vertical-first:   ``add_bend(pipe, x1, y2)``

        Parameters
        ----------
        pipe:
            A PIPE element.
        x:
            X coordinate of the new waypoint.
        y:
            Y coordinate of the new waypoint.
        index:
            Position in the waypoints list to insert at.  ``None`` (default)
            inserts before the last point, making the new point the corner
            of a start → corner → end L-shape.
        """
        return self._layout_service.add_bend(pipe, x, y, index)

    def snap_orthogonal(self, threshold_deg: float = 10.0) -> None:
        """Snap near-orthogonal connections to exactly horizontal or vertical.

        For each connected element pair whose angle deviates less than
        *threshold_deg* from horizontal or vertical, adjusts one element's
        position to make the connection perfectly orthogonal.

        Parameters
        ----------
        threshold_deg:
            Maximum deviation in degrees to trigger snapping. Defaults to 10.
        """
        return self._layout_service.snap_orthogonal(threshold_deg)

    def align_horizontal(self, names: list[str], anchor_y: float | None = None) -> None:
        """Align named elements to the same Y coordinate.

        Parameters
        ----------
        names:
            Element names to align.
        anchor_y:
            Target Y. If omitted, the mean Y of the group is used.
        """
        return self._layout_service.align_horizontal(names, anchor_y)

    def align_vertical(self, names: list[str], anchor_x: float | None = None) -> None:
        """Align named elements to the same X coordinate.

        Parameters
        ----------
        names:
            Element names to align.
        anchor_x:
            Target X. If omitted, the mean X of the group is used.
        """
        return self._layout_service.align_vertical(names, anchor_x)

    def distribute_horizontal(self, names: list[str]) -> None:
        """Space named elements evenly along the X axis.

        The leftmost and rightmost elements stay fixed; everything in between
        is redistributed with equal gaps.

        Parameters
        ----------
        names:
            Element names to distribute (at least 3 required for effect).
        """
        return self._layout_service.distribute_horizontal(names)

    def distribute_vertical(self, names: list[str]) -> None:
        """Space named elements evenly along the Y axis.

        The topmost and bottommost elements stay fixed; everything in between
        is redistributed with equal gaps.

        Parameters
        ----------
        names:
            Element names to distribute (at least 3 required for effect).
        """
        return self._layout_service.distribute_vertical(names)

    def snap_to_grid(self, grid_size: float = 500.0) -> None:
        """Round every placed element's position to the nearest grid point.

        Parameters
        ----------
        grid_size:
            Grid cell size in model units. Defaults to 500.
        """
        return self._layout_service.snap_to_grid(grid_size)

    def center_layout(self) -> None:
        """Translate all placed elements so the bounding box is centred on the canvas."""
        return self._layout_service.center_layout()

    def visualize(self, **kwargs: Any) -> str:
        """Create a text visualization of elements and connections.

        Returns:
            Multi-line string with model layout visualization.
        """
        return self._layout_service.visualize(**kwargs)

    def visualize_network(self, path: str | Path = "network.html") -> None:
        """Generate an interactive PyVis HTML visualization.

        Parameters
        ----------
        path:
            Output file path for the HTML visualization.
        """
        return self._layout_service.visualize_network(path)

    # I/O - delegate to IOService
    def save(
        self, path: str | Path | None = None, *, check_layout: bool = True, overwrite: bool = True
    ) -> None:
        """Serialize the (possibly modified) model back to a .kdf file.

        Parameters
        ----------
        path:
            Destination path. If *None*, overwrites the source file.
        check_layout:
            If True (default), validate layout before saving and warn about
            overlapping elements or elements outside bounds.
        overwrite:
            If True (default), allow overwriting existing files. If False,
            raise an error if the destination file already exists.
        """
        return self._io_service.save(path, check_layout=check_layout, overwrite=overwrite)

    def save_as(
        self, path: str | Path, *, check_layout: bool = True, overwrite: bool = False
    ) -> None:
        """Save to a new path (alias for :meth:`save` with a path argument)."""
        return self._io_service.save_as(path, check_layout=check_layout, overwrite=overwrite)

    def to_dataframes(self) -> dict:
        """Convert the model to a dict of DataFrames (one per element type).

        Each DataFrame preserves the raw KDF record lines so that the model
        can be perfectly reconstructed. Verbatim / header lines are stored
        in a ``"_HEADER"`` DataFrame.

        Returns:
            ``dict[str, pd.DataFrame]`` keyed by element type name.

        Raises:
            ExportError: If *pandas* is not installed.
        """
        return self._io_service.to_dataframes()

    def to_excel(self, path: str | Path) -> None:
        """Export the model to an Excel workbook with lossless round-trip fidelity.

        Each element type is written to a separate sheet. The workbook
        can be read back with :meth:`from_excel` to produce an identical
        ``.kdf`` file.

        Parameters
        ----------
        path:
            Destination ``.xlsx`` file path.

        Raises:
            ExportError: If *pandas* or *openpyxl* is not installed.
        """
        return self._io_service.to_excel(path)

    # SUMMARY - delegate to SummaryService
    def validate(self) -> list[str]:
        """Validate KDF format compliance.

        Returns:
            List of validation issues (empty = valid model).
        """
        return self._summary_service.validate()

    def pipe(self, index: int) -> Pipe:
        """Return pipe *index*, raise :exc:`ElementNotFound` if absent."""
        return self._summary_service.pipe(index)

    def pump(self, index: int) -> Pump:
        """Return pump *index*, raise :exc:`ElementNotFound` if absent."""
        return self._summary_service.pump(index)

    def feed(self, index: int) -> Feed:
        """Return feed *index*, raise :exc:`ElementNotFound` if absent."""
        return self._summary_service.feed(index)

    def product(self, index: int) -> Product:
        """Return product *index*, raise :exc:`ElementNotFound` if absent."""
        return self._summary_service.product(index)

    def reload(self) -> None:
        """Reload the model from disk.

        This method re-reads the .kdf file from disk and rebuilds all
        in-memory collections. Useful when the file has been modified
        externally (e.g., via KORF GUI) while the model is loaded in TUI.

        Raises:
            ParseError: If the file cannot be read or parsed.
        """
        self._parser.load()
        self._build_collections()
        self._loaded_mtime = self._parser.path.stat().st_mtime

    def summary(self) -> dict:
        """Return a high-level dict describing the model."""
        return self._summary_service.summary()

    def __repr__(self) -> str:
        return self._summary_service.__repr__()

    # classmethods that create Model instances
    @classmethod
    def from_dataframes(cls, dfs: dict) -> Model:
        """Create a Model from a dict of DataFrames.

        This is the inverse of :meth:`to_dataframes`.

        Args:
            dfs: Dict of DataFrames as returned by :meth:`to_dataframes`.

        Returns:
            A new :class:`Model` instance.

        Example:
            ```python
            dfs = model.to_dataframes()
            reconstructed = Model.from_dataframes(dfs)
            ```
        """
        return IOService.model_from_dataframes(dfs)

    @classmethod
    def from_excel(cls, path: str | Path) -> Model:
        """Create a Model from an Excel workbook.

        This is the inverse of :meth:`to_excel`.

        Args:
            path: Path to the ``.xlsx`` file.

        Returns:
            A new :class:`Model` instance.

        Example:
            ```python
            model = Model.from_excel("Pumpcases.xlsx")
            model.save("Pumpcases_roundtrip.kdf")
            ```
        """
        dfs = IOService.excel_to_dataframes(path)
        return IOService.model_from_dataframes(dfs)


KorfModel = Model

__all__ = ["KorfModel", "Model"]
