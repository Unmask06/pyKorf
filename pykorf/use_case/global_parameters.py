"""Global Settings presets for bulk model modifications.

This module provides preset functions that apply common global changes
to KDF models, such as modifying dummy pipes or applying design margins.

Global Settings:
    1. Dummy Pipe & Junction Labels - Modify dummy pipes and hide labels
       - Pipes starting with "d": Set LEN = 0.1 m, ID = 1.5 m, SCH = "ID", LBL = OFF
       - All Junctions: Set LBL = [0, 0, 50] (turn off labels)
    2. 25% margin in dP/dL - Apply DP_DES_FAC = 1.25 to all pipes
    3. Rename Line from NOTES - Extract fluid code and serial number from NOTES
       and update pipe name (e.g., "L4" -> "VCL17-806")
    4. Set PIPE Sizing Criteria - Apply SIZ criteria to all pipes
       - Set dP/dL criteria (default: 22.6 kPa/100m)
       - Set velocity bounds (default: 0.3-100 m/s)

Usage:
    >>> from pykorf import Model
    >>> from pykorf.use_case.global_parameters import apply_global_settings
    >>>
    >>> model = Model("model.kdf")
    >>> results = apply_global_settings(model, ["dummy_pipe", "dp_margin"])
    >>> for setting_id, pipes in results.items():
    >>>     print(f"{setting_id}: {len(pipes)} pipes affected")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

if TYPE_CHECKING:
    from pykorf.model import Model

logger = logging.getLogger("GlobalSettings")


@dataclass
class GlobalSetting:
    """Represents a global setting preset.

    Attributes:
        id: Unique identifier for the setting (e.g., "dummy_pipe", "dp_margin")
        name: Display name for the setting
        description: Detailed description of what the setting does
        apply_func: Function that applies setting to model, returns affected pipe names
    """

    id: str
    name: str
    description: str
    apply_func: Callable[..., list[str]]


def apply_dummy_pipe_settings(model: Model) -> list[str]:
    """Apply dummy pipe settings and hide junction labels.

    For each pipe whose name starts with lowercase "d":
    - Set LEN = 0.1 (meters)
    - Set ID = 1500 mm (converted to 1.5 meters)
    - Set SCH = "ID"
    - Set LBL = [0, 0, 50] (turn off labels)

    For all junctions:
    - Set LBL = [0, 0, 50] (turn off labels)

    Args:
        model: Loaded KDF model.

    Returns:
        List of pipe and junction names that were modified.
    """
    from pykorf.elements import Junction, Pipe
    from pykorf.exceptions import ParameterError

    affected_names: list[str] = []
    errors: list[str] = []

    # ID in meters (1500mm = 1.5m)
    id_meters = 1.5

    # 1. Iterate through all pipes (index >= 1 are real instances)
    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        pipe_name = pipe.name

        # Check if pipe name starts with lowercase "d"
        if not pipe_name or not pipe_name.startswith("d"):
            continue

        # Apply the settings - format matches apply_pms pattern
        # LEN needs 2 values: [value, unit]
        # ID needs 3 values: [value1, value2, unit] based on template
        # LBL needs 3 values: [on/off, x_offset, font_size] - 0=off, -1=on
        params: dict[str, Any] = {
            Pipe.LEN: [0.1, "m"],
            Pipe.SCH: "ID",
            Pipe.ID: [str(id_meters), str(id_meters), "m"],
            Pipe.LBL: [0, 0, 50],  # Turn off labels (0=off, 0=x_offset, 50=font_size)
        }

        try:
            model.set_params(pipe_name, params)
            affected_names.append(pipe_name)
            logger.info(
                "Dummy pipe %s: LEN=0.1m, ID=%sm (1500mm), SCH=ID, LBL=OFF",
                pipe_name,
                id_meters,
            )
        except ParameterError as e:
            error_msg = f"Validation error on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error setting params on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    # 2. Iterate through all junctions (index >= 1)
    for idx, junc in model.junctions.items():
        if idx == 0:
            continue
        junc_name = junc.name
        if not junc_name:
            continue

        try:
            model.set_params(junc_name, {Junction.LBL: [0, 0, 50]})
            affected_names.append(junc_name)
            logger.info("Junction %s: LBL=OFF", junc_name)
        except Exception as e:
            error_msg = f"Error setting LBL on junction {junc_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return affected_names


def apply_dp_margin_settings(model: Model, margin: float = 1.25) -> list[str]:
    """Apply margin to pressure drop design factor for all pipes.

    Sets DP_DES_FAC on all pipes, providing a margin on pressure drop calculations.

    Args:
        model: Loaded KDF model.
        margin: Design margin factor (default 1.25 for 25% margin).

    Returns:
        List of pipe names that were modified.
    """
    from pykorf.elements import Pipe
    from pykorf.exceptions import ParameterError

    affected_pipes: list[str] = []
    errors: list[str] = []

    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        pipe_name = pipe.name

        params: dict[str, Any] = {
            Pipe.DP_DES_FAC: margin,
        }

        try:
            model.set_params(pipe_name, params)
            affected_pipes.append(pipe_name)
            logger.info(
                "Pipe %s: DP_DES_FAC=%s (%s%% margin)", pipe_name, margin, int((margin - 1) * 100)
            )
        except ParameterError as e:
            error_msg = f"Validation error on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error setting params on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return affected_pipes


def apply_rename_line_settings(model: Model) -> list[str]:
    """Rename pipes using fluid code and serial number from NOTES field.

    For all pipes with valid NOTES line numbers:
    - Extract fluid code and serial number from NOTES (e.g., "VCL17-806")
    - Update first element of NAME with extracted value
    - Retain second element (description) unchanged
    - Add suffix (_1, _2, etc.) if name already exists

    Args:
        model: Loaded KDF model.

    Returns:
        List of pipe names that were modified.
    """
    from pykorf.elements import Pipe
    from pykorf.elements.pipe import propagate_pipe_rename
    from pykorf.exceptions import ParameterError
    from pykorf.use_case.line_number import extract_fluid_seq_from_notes

    affected_pipes: list[str] = []
    errors: list[str] = []
    used_names: set[str] = set()

    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        pipe_name = pipe.name

        notes_rec = pipe.get_param("NOTES")
        if notes_rec is None or not notes_rec.values or not notes_rec.values[0]:
            logger.debug("Pipe %s: skipping, NOTES is empty", pipe_name)
            continue

        notes_value = notes_rec.values[0]
        extracted = extract_fluid_seq_from_notes(notes_value)

        if extracted is None:
            logger.debug("Pipe %s: skipping, cannot parse NOTES: %s", pipe_name, notes_value)
            continue

        name_rec = pipe.get_param("NAME")
        if name_rec is None or not name_rec.values:
            logger.warning("Pipe %s: skipping, NAME record not found", pipe_name)
            continue

        if len(name_rec.values) < 1:
            logger.warning("Pipe %s: skipping, NAME has no values", pipe_name)
            continue

        second_element = name_rec.values[1] if len(name_rec.values) > 1 else "Pipe"

        new_name = extracted
        if len(new_name) > 12:
            logger.warning(
                "Pipe %s: extracted name %s exceeds 12 char limit, skipping",
                pipe_name,
                extracted,
            )
            continue

        if new_name in used_names:
            suffix_num = 1
            while True:
                new_name = f"{extracted}_{suffix_num}"
                if len(new_name) > 12:
                    logger.warning(
                        "Pipe %s: generated name %s exceeds 12 char limit, skipping",
                        pipe_name,
                        new_name,
                    )
                    new_name = None
                    break
                if new_name not in used_names:
                    break
                suffix_num += 1

            if new_name is None:
                continue

        used_names.add(new_name)

        try:
            new_name_values = [new_name, second_element]
            model.set_params(pipe_name, {Pipe.NAME: new_name_values})
            affected_pipes.append(pipe_name)
            logger.info("Pipe %s: renamed to %s", pipe_name, new_name)

            # Propagate rename to any EQN records that reference this pipe by name
            eqn_updated = propagate_pipe_rename(model, pipe_name, new_name)
            if eqn_updated:
                logger.info(
                    "Pipe %s: EQN reference updated in %d pipe(s): %s",
                    new_name,
                    len(eqn_updated),
                    eqn_updated,
                )
        except ParameterError as e:
            error_msg = f"Validation error on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error setting params on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return affected_pipes


def set_pipe_criteria(
    model: Model,
    dpdl_criteria: float = 22.6,
    dpdl_unit: str = "kPa/100m",
    max_vel: float = 100,
    min_vel: float = 0.3,
    max_coeff: float = 120,
    min_coeff: float = 10,
    vel_unit: str = "m/s",
) -> list[str]:
    """Set PIPE sizing criteria (SIZ parameter) for all pipes.

    This function sets the SIZ parameter on all pipes in the model with the specified
    criteria values. The SIZ parameter defines the validation criteria for pressure
    drop and velocity checks.

    Args:
        model: Loaded KDF model.
        dpdl_criteria: Pressure drop per length criteria (default: 22.6).
        dpdl_unit: Pressure drop unit (default: "kPa/100m").
        max_vel: Maximum allowable velocity (default: 100).
        min_vel: Minimum allowable velocity (default: 0.3).
        max_coeff: Maximum velocity coefficient (default: 120).
        min_coeff: Minimum velocity coefficient (default: 10).
        vel_unit: Velocity unit (default: "m/s").

    Returns:
        List of pipe names that were modified.

    Example::

        set_pipe_criteria(
            model,
            dpdl_criteria=30.0,
            max_vel=50,
            min_vel=0.5,
        )
    """
    from pykorf.elements import Pipe
    from pykorf.exceptions import ParameterError

    affected_pipes: list[str] = []
    errors: list[str] = []

    siz_values = ["", dpdl_criteria, dpdl_unit, max_vel, min_vel, max_coeff, min_coeff, vel_unit]

    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        pipe_name = pipe.name

        params: dict[str, Any] = {
            Pipe.SIZ: siz_values,
        }

        try:
            model.set_params(pipe_name, params)
            affected_pipes.append(pipe_name)
            logger.info(
                "Pipe %s: SIZ criteria set (dP/dL=%s %s, vel=%.1f-%.1f m/s)",
                pipe_name,
                dpdl_criteria,
                dpdl_unit,
                min_vel,
                max_vel,
            )
        except ParameterError as e:
            error_msg = f"Validation error on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error setting params on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return affected_pipes


def apply_pipe_criteria_settings(model: Model) -> list[str]:
    """Apply default PIPE sizing criteria to all pipes.

    Sets SIZ parameter with default criteria:
    - dP/dL: 22.6 kPa/100m
    - Max velocity: 100 m/s
    - Min velocity: 0.3 m/s

    Args:
        model: Loaded KDF model.

    Returns:
        List of pipe names that were modified.
    """
    return set_pipe_criteria(model)


# Registry of all available global settings
_GLOBAL_SETTINGS: dict[str, GlobalSetting] = {
    "dummy_pipe": GlobalSetting(
        id="dummy_pipe",
        name="Dummy Pipe & Junction Labels",
        description='Pipes starting with "d": LEN=0.1m, ID=1500mm, LBL=OFF. Junctions: LBL=OFF',
        apply_func=apply_dummy_pipe_settings,
    ),
    "dp_margin": GlobalSetting(
        id="dp_margin",
        name="Margin in dP/dL",
        description="Set DP_DES_FAC on all pipes for pressure drop design margin",
        apply_func=apply_dp_margin_settings,
    ),
    "rename_line": GlobalSetting(
        id="rename_line",
        name="Rename Line from NOTES",
        description="Extract fluid code + serial number from NOTES, update pipe name",
        apply_func=apply_rename_line_settings,
    ),
    "pipe_criteria": GlobalSetting(
        id="pipe_criteria",
        name="Set PIPE Sizing Criteria",
        description="Set default SIZ criteria (dP/dL=22.6 kPa/100m, vel=0.3-100 m/s) on all pipes",
        apply_func=apply_pipe_criteria_settings,
    ),
}


def get_global_settings() -> list[GlobalSetting]:
    """Return list of all available global settings.

    Returns:
        List of GlobalSetting instances, ordered by their registration order.
    """
    return list(_GLOBAL_SETTINGS.values())


def get_global_setting(setting_id: str) -> GlobalSetting | None:
    """Get a specific global setting by its ID.

    Args:
        setting_id: The unique identifier of the setting.

    Returns:
        GlobalSetting instance if found, None otherwise.
    """
    return _GLOBAL_SETTINGS.get(setting_id)


def apply_global_settings(
    model: Model,
    setting_ids: list[str],
    *,
    save: bool = True,
    dp_margin: float = 1.25,
) -> dict[str, list[str]]:
    """Apply selected global settings to a model.

    Args:
        model: Loaded KDF model.
        setting_ids: List of setting IDs to apply (e.g., ["dummy_pipe", "dp_margin"]).
        save: Whether to save the model after applying changes (default True).
        dp_margin: Design margin factor for dp_margin setting (default 1.25).

    Returns:
        Dictionary mapping setting IDs to lists of affected pipe names.
        The special key "_errors" contains list of error messages if any.

    Example:
        >>> from pykorf import Model
        >>> from pykorf.use_case.global_parameters import apply_global_settings
        >>>
        >>> model = Model("model.kdf")
        >>> results = apply_global_settings(model, ["dummy_pipe", "dp_margin"])
        >>> print(results)
        {'dummy_pipe': ['d1', 'd2'], 'dp_margin': ['L1', 'L2', 'P1'], '_errors': []}
    """
    results: dict[str, list[str]] = {}
    all_errors: list[str] = []

    for setting_id in setting_ids:
        setting = _GLOBAL_SETTINGS.get(setting_id)
        if setting is None:
            logger.warning("Unknown global setting: %s", setting_id)
            all_errors.append(f"Unknown setting: {setting_id}")
            continue

        try:
            # Pass dp_margin parameter to the dp_margin setting
            if setting_id == "dp_margin":
                affected = setting.apply_func(model, margin=dp_margin)
            else:
                affected = setting.apply_func(model)
            results[setting_id] = affected
            logger.info(
                "Applied setting '%s' to %d pipes",
                setting.name,
                len(affected),
            )
        except Exception as e:
            error_msg = f"Error applying setting '{setting_id}': {e}"
            logger.error(error_msg)
            all_errors.append(error_msg)
            results[setting_id] = []

    if all_errors:
        results["_errors"] = all_errors

    if save and results:
        model.save()

    return results
