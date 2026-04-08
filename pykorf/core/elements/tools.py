r"""Tools element (``\\TOOLS``)."""

from __future__ import annotations

from pykorf.core.elements.base import BaseElement


class Tools(BaseElement):
    r"""Wraps ``\\TOOLS`` records - internal tool configuration data.

    This is a lightweight stub carrying only the KDF parameter constants.
    """

    ETYPE = "TOOLS"
    ENAME = "Tools"

    # ------------------------------------------------------------------
    # Parameter constants (moved from definitions/tools.py)
    # ------------------------------------------------------------------
    PIPEI = "PIPEI"  # [name, type, flow, flow_unit, ..., ..., den_unit, ..., visc_unit, ..., ..., ..., dia, dia_unit, sch, roughness, unit]
    PIPEOA = "PIPEOA"  # [elev, unit, ..., vel_unit, ..., ..., ..., ..., ..., ..., ..., dpl_unit, ..., ...]
    PIPEOB = "PIPEOB"  # [???, ???]
    VALVEI = "VALVEI"  # [name, type, flow, flow_unit, ..., ..., den_unit, ..., visc_unit, ..., ..., ..., ..., ..., ..., ..., pres_unit, xt]
    VALVEO = "VALVEO"  # [???, ???]
    FOI = "FOI"  # [name, type, flow, flow_unit, ..., ..., den_unit, ..., visc_unit, ..., ..., ..., ..., ..., ..., ..., pres_unit, beta, ..., unit, type, holes]
    FOO = "FOO"  # [..., ..., unit, ..., ..., ..., ..., pres_unit]

    ALL = (PIPEI, PIPEOA, PIPEOB, VALVEI, VALVEO, FOI, FOO)
