"""Query and filter functionality for pyKorf models.

This module is deprecated. Use the direct methods on Model instead:
- Model.get_elements() - Get elements with optional filtering
- Model.get_params() - Get element parameters
- Model.set_params() - Set element parameters

Example:
    >>> from pykorf import Model
    >>>
    >>> model = Model("Pumpcases.kdf")
    >>>
    >>> # Get all pipes
    >>> pipes = model.get_elements(etype="PIPE")
    >>>
    >>> # Get elements by name pattern
    >>> p_elements = model.get_elements(name="P*")
    >>>
    >>> # Get parameters
    >>> all_params = model.get_params("P1")
    >>> len_record = model.get_params("P1", param="LEN")
    >>>
    >>> # Set parameters
    >>> model.set_params("P1", {"LEN": 200, "DIAM": 50})
"""

from __future__ import annotations

import warnings

# Deprecation warning when this module is imported
warnings.warn(
    "The query module is deprecated. Use Model.get_elements(), "
    "Model.get_params(), and Model.set_params() instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = []
