"""Results – extract calculated output values from a run KORF model.

After KORF calculates a model and it is saved back to .kdf, the result
values are embedded in the file.  This module provides convenient
accessors without requiring you to parse the raw token lists yourself.

Example::

    from pykorf import KorfModel, Results

    model = KorfModel.load("Pumpcases.kdf")  # file already calculated
    res = Results(model)

    print(res.pump_summary(1))
    #  {'name': 'P1', 'head_m': 155.6, 'power_kW': 24.16, 'efficiency': 0.351}

    print(res.pipe_velocities())
    #  {1: [0.298, 0.298, 0.298, 0.0], 2: [0.676, ...], ...}

    df = res.to_dataframe()  # requires pandas
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykorf.model import KorfModel


class Results:
    """Wrapper that exposes calculated KORF results from a loaded model.

    Parameters
    ----------
    model:
        A :class:`KorfModel` that has been saved after running in KORF.
    """

    def __init__(self, model: KorfModel):
        self._model = model

    # ------------------------------------------------------------------
    # Pumps
    # ------------------------------------------------------------------

    def pump_summary(self, index: int) -> dict:
        """Key calculated results for pump *index*.

        Returns:
        -------
        dict with keys: name, head_m, flow_m3h, power_kW, efficiency,
        npsh_required_m, dp_kPag.
        """
        p = self._model.pump(index)
        return {
            "name": p.name,
            "head_m": p.head_m,
            "flow_m3h": p.flow_m3h,
            "power_kW": p.power_kW,
            "efficiency": p.efficiency,
            "npsh_required_m": p.npsh_required_m,
            "dp_kPag": p.dp_kPag,
        }

    def all_pump_results(self) -> list[dict]:
        """Return pump_summary for every real pump (index > 0)."""
        return [self.pump_summary(idx) for idx in sorted(self._model.pumps) if idx > 0]

    # ------------------------------------------------------------------
    # Pipes
    # ------------------------------------------------------------------

    def pipe_velocities(self) -> dict[int, list[float]]:
        """Return {pipe_index: [velocity_case1, …]} for all real pipes."""
        return {idx: pipe.velocity for idx, pipe in self._model.pipes.items() if idx > 0}

    def pipe_pressures(self) -> dict[int, list[float]]:
        """Return {pipe_index: [pressure_case1, …]} for all real pipes."""
        return {idx: pipe.pressure for idx, pipe in self._model.pipes.items() if idx > 0}

    def pipe_dp_per_100m(self) -> dict[int, float]:
        return {
            idx: pipe.pressure_drop_per_100m for idx, pipe in self._model.pipes.items() if idx > 0
        }

    # ------------------------------------------------------------------
    # Valves / orifices
    # ------------------------------------------------------------------

    def valve_dp(self) -> dict[int, float]:
        return {idx: v.dp_kPag for idx, v in self._model.valves.items() if idx > 0}

    def orifice_dp(self) -> dict[int, float]:
        return {idx: o.dp_kPag for idx, o in self._model.orifices.items() if idx > 0}

    # ------------------------------------------------------------------
    # Compressors
    # ------------------------------------------------------------------

    def compressor_summary(self, index: int) -> dict:
        c = self._model.compressors[index]
        return {
            "name": c.name,
            "power_kW": c.power_kW,
            "head_m": c.head_m,
            "efficiency": c.efficiency,
            "dp_kPag": c.dp_kPag,
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_dataframe(self):
        """Export all pump and pipe results to a ``pandas.DataFrame``.

        Requires ``pandas`` to be installed.

        Returns:
        -------
        pandas.DataFrame
            One row per element with columns: element_type, index, name,
            and all numeric result fields.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "pandas is required for Results.to_dataframe(). Install it with: pip install pandas"
            ) from exc

        rows = []
        for r in self.all_pump_results():
            rows.append({"element_type": "PUMP", **r})
        for idx, pipe in self._model.pipes.items():
            if idx == 0:
                continue
            rows.append(
                {
                    "element_type": "PIPE",
                    "name": pipe.name,
                    "index": idx,
                    "dP_kPa_100m": pipe.pressure_drop_per_100m,
                    "Re": pipe.reynolds_number,
                    "velocity_ms": pipe.velocity,
                }
            )
        return pd.DataFrame(rows)

    def __repr__(self) -> str:
        return f"Results(model={self._model!r})"
