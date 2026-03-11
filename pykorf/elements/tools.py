"""Tools element (``\\TOOLS``)."""

from __future__ import annotations

from pykorf.elements.base import BaseElement


class Tools(BaseElement):
    """Wraps ``\\TOOLS`` records - internal tool configuration data.

    This is a lightweight stub carrying only the KDF parameter constants.
    """

    ETYPE = "TOOLS"
    ENAME = "Tools"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/tools.py)
    # ------------------------------------------------------------------
    PIPEI = "PIPEI"
    PIPEOA = "PIPEOA"
    PIPEOB = "PIPEOB"
    VALVEI = "VALVEI"
    VALVEO = "VALVEO"
    FOI = "FOI"
    FOO = "FOO"

    ALL = (PIPEI, PIPEOA, PIPEOB, VALVEI, VALVEO, FOI, FOO)
