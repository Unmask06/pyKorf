"""CaseSet - helpers for managing multi-case scenarios in a KORF model.

KORF supports running multiple scenarios (cases) in a single file.
Each case is identified by its 1-based position in the semicolon-delimited
value strings stored in the .kdf.

Example::

    from pykorf import KorfModel, CaseSet

    model = KorfModel.load("Pumpcases.kdf")
    cases = CaseSet(model)

    print(cases.names)  # ['NORMAL', 'RATED', 'MINIMUM']
    cases.set_pipe_flows(1, [50, 55, 20])
    cases.set_feed_pressures(1, [50, 60, 40])

    # Run only case 2 in KORF
    cases.activate_cases([2])
    model.save()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykorf.exceptions import CaseError
from pykorf.utils import join_cases, split_cases

if TYPE_CHECKING:
    from pykorf.model import KorfModel


class CaseSet:
    """Multi-case management helper.

    Parameters
    ----------
    model:
        A loaded :class:`KorfModel`.
    """

    def __init__(self, model: KorfModel):
        self._model = model

    # ------------------------------------------------------------------
    # Case metadata
    # ------------------------------------------------------------------

    @property
    def names(self) -> list[str]:
        """Case description strings, e.g. ``['NORMAL', 'RATED', 'MINIMUM']``."""
        return self._model.general.case_descriptions

    @property
    def numbers(self) -> list[str]:
        """Active case numbers, e.g. ``['1', '2', '3']``."""
        return self._model.general.case_numbers

    @property
    def count(self) -> int:
        return self._model.general.num_cases

    def _validate_case(self, case_index: int) -> None:
        if case_index < 1 or case_index > self.count:
            raise CaseError(f"Case index {case_index} out of range 1-{self.count}")

    # ------------------------------------------------------------------
    # Activate / deactivate cases
    # ------------------------------------------------------------------

    def activate_cases(self, case_indices: list[int]) -> None:
        """Set the active cases to run (by 1-based index).

        Updates both ``CASENO`` (which cases are active) and ``CASERPT``
        (which cases to include in the report).

        Parameters
        ----------
        case_indices:
            List of 1-based indices, e.g. ``[1, 2]``.
        """
        for ci in case_indices:
            self._validate_case(ci)
        no_str = ";".join(str(i) for i in case_indices)
        rpt_vals = ["1" if (i + 1) in case_indices else "0" for i in range(self.count)]
        rpt_str = ";".join(rpt_vals)
        self._model._parser.set_value("GEN", 0, "CASENO", [no_str])
        self._model._parser.set_value("GEN", 0, "CASERPT", [rpt_str])

    # ------------------------------------------------------------------
    # Bulk value setters
    # ------------------------------------------------------------------

    def set_pipe_flows(self, pipe_index: int, flows: list) -> None:
        """Set flow values for all cases on pipe *pipe_index*.

        Parameters
        ----------
        pipe_index:
            1-based pipe index.
        flows:
            List of flow values (one per case), e.g. ``[50, 55, 20]``.
        """
        self._model.pipe(pipe_index).set_flow(flows)

    def set_feed_pressures(self, feed_index: int, pressures: list) -> None:
        """Set feed pressures for all cases."""
        self._model.feed(feed_index).set_pressure(pressures)

    def set_product_pressures(self, prod_index: int, pressures: list) -> None:
        """Set product (back-pressure) for all cases."""
        self._model.product(prod_index).set_pressure(pressures)

    def get_case_value(self, raw_string: str, case_index: int) -> str:
        """Extract the value for *case_index* (1-based) from a semicolon string.

        ``'50;55;20'``.

        Parameters
        ----------
        raw_string:
            A KORF multi-case string.
        case_index:
            1-based case position.
        """
        parts = split_cases(raw_string)
        self._validate_case(case_index)
        if len(parts) == 1:
            return parts[0]  # single value applies to all cases
        return parts[case_index - 1]

    def set_case_value(self, raw_string: str, case_index: int, new_value: str) -> str:
        """Replace the value for *case_index* in *raw_string*.

        Returns the updated string.

        Parameters
        ----------
        raw_string:
            Existing multi-case string, e.g. ``'50;55;20'``.
        case_index:
            1-based position to update.
        new_value:
            Replacement value as a string.
        """
        parts = split_cases(raw_string)
        self._validate_case(case_index)
        # Expand single-value strings to full length if needed
        if len(parts) == 1 and self.count > 1:
            parts = parts * self.count
        parts[case_index - 1] = str(new_value)
        return join_cases(parts)

    # ------------------------------------------------------------------
    # Tabular summary
    # ------------------------------------------------------------------

    def pipe_flows_table(self) -> list[dict]:
        """Return a list of dicts - one row per pipe - showing flow per case.

        Useful for display::

            import pprint

            pprint.pprint(cases.pipe_flows_table())
        """
        rows = []
        for idx, pipe in self._model.pipes.items():
            if idx == 0:
                continue
            flow_parts = split_cases(pipe.flow_string)
            row = {"pipe": pipe.name, "index": idx}
            for ci, name in enumerate(self.names, 1):
                val = flow_parts[ci - 1] if ci <= len(flow_parts) else flow_parts[-1]
                row[name] = val
            rows.append(row)
        return rows
