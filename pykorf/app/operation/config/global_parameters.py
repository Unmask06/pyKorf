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

Usage:
    >>> from pykorf import Model
    >>> from pykorf.app.operation.config.global_parameters import apply_global_settings
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
    from pykorf.core.model import Model

logger = logging.getLogger(__name__)


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
    from pykorf.core.elements import Junction, Pipe
    from pykorf.core.exceptions import ParameterError

    affected_names: list[str] = []
    errors: list[str] = []

    # ID in meters (1500mm = 1.5m)
    id_meters = 1.5

    # 1. Iterate through all pipes (index >= 1 are real instances)
    if model.num_pipes > 0:
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
    if model.num_junctions > 0:
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


def apply_dp_margin_settings(model: Model, margin: float) -> list[str]:
    """Apply margin to pressure drop design factor for all pipes.

    Sets DP_DES_FAC on all pipes, providing a margin on pressure drop calculations.

    Args:
        model: Loaded KDF model.
        margin: Design margin factor (default 1.25 for 25% margin).

    Returns:
        List of pipe names that were modified.
    """
    from pykorf.core.elements import Pipe
    from pykorf.core.exceptions import ParameterError

    if model.num_pipes <= 0:
        return []

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
    from pykorf.app.operation.data_import.line_number import extract_fluid_seq_from_notes
    from pykorf.core.elements import Pipe
    from pykorf.core.elements.pipe import propagate_pipe_rename
    from pykorf.core.exceptions import ParameterError

    if model.num_pipes <= 0:
        return []

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
        if len(new_name) > 20:
            logger.warning(
                "Pipe %s: extracted name %s exceeds 20 char limit, skipping",
                pipe_name,
                extracted,
            )
            continue

        if new_name in used_names:
            suffix_num = 1
            while True:
                new_name = f"{extracted}_{suffix_num}"
                if len(new_name) > 20:
                    logger.warning(
                        "Pipe %s: generated name %s exceeds 20 char limit, skipping",
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


def apply_pump_shutoff_settings(model: Model, margin: float) -> list[str]:
    """Set shutoff DP margin for all pumps.

    Sets PZRAT on all pumps, providing a margin on the shutoff pressure calculation.
    The shutoff margin is applied as a multiplier on the calculated DP at shutoff.

    Args:
        model: Loaded KDF model.
        margin: Shutoff DP margin factor (default 1.20 for 20% margin).

    Returns:
        List of pump names that were modified.
    """
    from pykorf.core.elements import Pump
    from pykorf.core.exceptions import ParameterError

    if model.num_pumps <= 0:
        return []

    affected_pumps: list[str] = []
    errors: list[str] = []

    for idx in range(1, model.num_pumps + 1):
        pump = model.pumps[idx]
        pump_name = pump.name

        # Preserve existing method and flag; update only the margin value
        pzrat_rec = pump.get_param("PZRAT")
        if pzrat_rec and pzrat_rec.values and len(pzrat_rec.values) >= 3:
            method = pzrat_rec.values[0]
            flag = pzrat_rec.values[2]
        else:
            method = "dPcalc"
            flag = 1

        params: dict[str, Any] = {
            Pump.SHUTOFF_DP_MARGIN: [method, margin, flag],
        }

        try:
            model.set_params(pump_name, params)
            affected_pumps.append(pump_name)
            logger.info(
                "Pump %s: PZRAT margin set to %s (%s%% margin)",
                pump_name,
                margin,
                int((margin - 1) * 100),
            )
        except ParameterError as e:
            error_msg = f"Validation error on {pump_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error setting params on {pump_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return affected_pumps


def apply_min_pump_elevation(model: Model, elevation: float) -> list[str]:
    """Set elevation of pumps that have a current elevation below the specified minimum.

    The specified elevation is treated as a minimum — pumps already at or above it
    are left unchanged. This prevents overwriting intentionally higher elevations.

    Args:
        model: Loaded KDF model.
        elevation: Minimum elevation value (m). Only pumps below this are updated.

    Returns:
        List of pump names that were modified.
    """
    from pykorf.core.elements import Pump
    from pykorf.core.exceptions import ParameterError

    if model.num_pumps <= 0:
        return []

    affected_pumps: list[str] = []
    errors: list[str] = []

    for idx in range(1, model.num_pumps + 1):
        pump = model.pumps[idx]
        pump_name = pump.name

        # Read existing elevation; skip if already at or above the minimum
        elev_rec = pump.get_param(Pump.ELEV)
        if elev_rec and elev_rec.values:
            try:
                current_elev = float(elev_rec.values[0])
                if current_elev > elevation:
                    logger.debug(
                        "Pump %s: ELEV %.1f m already exceeds minimum %.1f m, skipping",
                        pump_name,
                        current_elev,
                        elevation,
                    )
                    continue
            except (TypeError, ValueError):
                pass  # unparseable — fall through and apply

        params: dict[str, Any] = {
            Pump.ELEV: [elevation, "m"],
        }

        try:
            model.set_params(pump_name, params)
            affected_pumps.append(pump_name)
            logger.info("Pump %s: ELEV set to %.1f m", pump_name, elevation)
        except ParameterError as e:
            error_msg = f"Validation error on {pump_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error setting params on {pump_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return affected_pumps


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
        description="Set design margin for frictional pressure drop on all pipes",
        apply_func=apply_dp_margin_settings,
    ),
    "rename_line": GlobalSetting(
        id="rename_line",
        name="Rename Line from NOTES",
        description="Extract fluid code + serial number from NOTES, update pipe name",
        apply_func=apply_rename_line_settings,
    ),
    "pump_shutoff": GlobalSetting(
        id="pump_shutoff",
        name="Pump Raise-Shutoff Margin",
        description="Set shutoff DP margin on all pumps",
        apply_func=apply_pump_shutoff_settings,
    ),
    "min_pump_elevation": GlobalSetting(
        id="min_pump_elevation",
        name="Pump Elevation",
        description="Set minimum elevation for pumps; only updates pumps below specified elevation",
        apply_func=apply_min_pump_elevation,
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
    dp_margin: float,
    shutoff_margin: float,
    min_pump_elevation: float,
) -> dict[str, list[str]]:
    """Apply selected global settings to a model.

    Args:
        model: Loaded KDF model.
        setting_ids: List of setting IDs to apply (e.g., ["dummy_pipe", "dp_margin"]).
        save: Whether to save the model after applying changes (default True).
        dp_margin: Design margin factor for dp_margin setting.
        shutoff_margin: Shutoff DP margin factor for pump_shutoff setting.
        min_pump_elevation: Minimum elevation value for pump_elevation setting.

    Returns:
        Dictionary mapping setting IDs to lists of affected pipe names.
        The special key "_errors" contains list of error messages if any.

    Example:
        >>> from pykorf import Model
        >>> from pykorf.app.operation.config.global_parameters import apply_global_settings
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
            if setting_id == "dp_margin":
                affected = setting.apply_func(model, margin=dp_margin)
            elif setting_id == "pump_shutoff":
                affected = setting.apply_func(model, margin=shutoff_margin)
            elif setting_id == "min_pump_elevation":
                affected = setting.apply_func(model, elevation=min_pump_elevation)
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
        from pykorf.app.api.session_state import reload_sync

        reload_sync()

    return results
