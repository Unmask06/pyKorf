"""Global Settings presets for bulk model modifications.

This module provides preset functions that apply common global changes
to KDF models, such as modifying dummy pipes or applying design margins.

Global Settings:
    1. Set ID/Length for Dummy Pipe - Pipes with names starting with "d"
       - Set LEN = 0.1 m
       - Set ID = 1500 mm (converted to meters: 1.5 m)
       - Set SCH = "ID"
    2. 25% margin in dP/dL - Apply DP_DES_FAC = 1.25 to all pipes

Usage:
    >>> from pykorf import Model
    >>> from pykorf.use_case.global_settings import apply_global_settings
    >>>
    >>> model = Model("model.kdf")
    >>> results = apply_global_settings(model, ["dummy_pipe", "dp_margin"])
    >>> for setting_id, pipes in results.items():
    >>>     print(f"{setting_id}: {len(pipes)} pipes affected")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from pykorf.model import Model

logger = logging.getLogger(__name__)


@dataclass
class GlobalSetting:
    """Represents a global setting preset.

    Attributes:
        id: Unique identifier for the setting (e.g., "dummy_pipe", "dp_margin")
        name: Display name for the setting
        description: Detailed description of what the setting does
        apply_func: Function that applies the setting to a model and returns list of affected pipe names
    """

    id: str
    name: str
    description: str
    apply_func: Callable[["Model"], list[str]]


def apply_dummy_pipe_settings(model: "Model") -> list[str]:
    """Apply dummy pipe settings to all pipes with names starting with "d".

    For each pipe whose name starts with lowercase "d":
    - Set LEN = 0.1 (meters)
    - Set ID = 1500 mm (converted to 1.5 meters)
    - Set SCH = "ID"

    Args:
        model: Loaded KDF model.

    Returns:
        List of pipe names that were modified.
    """
    from pykorf.elements import Pipe
    from pykorf.exceptions import ParameterError

    affected_pipes: list[str] = []
    errors: list[str] = []

    # ID in meters (1500mm = 1.5m)
    id_meters = 1.5

    # Iterate through all pipes (index >= 1 are real instances)
    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        pipe_name = pipe.name

        # Check if pipe name starts with lowercase "d"
        if not pipe_name or not pipe_name.startswith("d"):
            continue

        # Apply the settings - format matches apply_pms pattern
        # LEN needs 2 values: [value, unit]
        # ID needs 3 values: [value1, value2, unit] based on template
        params: dict[str, Any] = {
            Pipe.LEN: [0.1, "m"],
            Pipe.SCH: "ID",
            Pipe.ID: [str(id_meters), str(id_meters), "m"],
        }

        try:
            model.set_params(pipe_name, params)
            affected_pipes.append(pipe_name)
            logger.info(
                "Dummy pipe %s: LEN=0.1m, ID=%sm (1500mm), SCH=ID",
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

    return affected_pipes


def apply_dp_margin_settings(model: "Model") -> list[str]:
    """Apply 25% margin to pressure drop design factor for all pipes.

    Sets DP_DES_FAC = 1.25 on all pipes, providing a 25% margin
    on the pressure drop calculations.

    Args:
        model: Loaded KDF model.

    Returns:
        List of pipe names that were modified.
    """
    from pykorf.elements import Pipe
    from pykorf.exceptions import ParameterError

    affected_pipes: list[str] = []
    errors: list[str] = []

    # Apply to all pipes (index >= 1 are real instances)
    for idx in range(1, model.num_pipes + 1):
        pipe = model.pipes[idx]
        pipe_name = pipe.name

        params: dict[str, Any] = {
            Pipe.DP_DES_FAC: 1.25,
        }

        try:
            model.set_params(pipe_name, params)
            affected_pipes.append(pipe_name)
            logger.info("Pipe %s: DP_DES_FAC=1.25 (25%% margin)", pipe_name)
        except ParameterError as e:
            error_msg = f"Validation error on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error setting params on {pipe_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    return affected_pipes


# Registry of all available global settings
_GLOBAL_SETTINGS: dict[str, GlobalSetting] = {
    "dummy_pipe": GlobalSetting(
        id="dummy_pipe",
        name="Set ID/Length for Dummy Pipe",
        description='Pipes with names starting with "d": Set LEN=0.1m, ID=1500 mm, SCH="ID"',
        apply_func=apply_dummy_pipe_settings,
    ),
    "dp_margin": GlobalSetting(
        id="dp_margin",
        name="25% margin in dP/dL",
        description="Set DP_DES_FAC=1.25 on all pipes for 25% pressure drop margin",
        apply_func=apply_dp_margin_settings,
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
    model: "Model",
    setting_ids: list[str],
    *,
    save: bool = True,
) -> dict[str, list[str]]:
    """Apply selected global settings to a model.

    Args:
        model: Loaded KDF model.
        setting_ids: List of setting IDs to apply (e.g., ["dummy_pipe", "dp_margin"]).
        save: Whether to save the model after applying changes (default True).

    Returns:
        Dictionary mapping setting IDs to lists of affected pipe names.
        The special key "_errors" contains list of error messages if any.

    Example:
        >>> from pykorf import Model
        >>> from pykorf.use_case.global_settings import apply_global_settings
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
