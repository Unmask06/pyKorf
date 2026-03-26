"""Rotating tips shown on the file picker screen."""

from __future__ import annotations

import random

TIPS: list[str] = [
    "💡 Multi-case values? Separate them with semicolons — e.g. '10;20;30' runs all three cases at once.",
    "💡 The ▲ badge on Config Menu means your source Excel has changed since last import — don't forget to re-import!",
    "💡 Apply PMS in one click: it auto-fills pipe schedule, material, rating and wall thickness from your spec sheet.",
    "💡 Apply HMB wires your heat & mass balance directly onto the model — no manual copy-pasting needed.",
    "💡 Gen. Report bundles all pipe results into a tidy Excel summary — great for design reviews.",
    "💡 Bulk Copy lets you push fluid properties from one element to many — a real time-saver on large models.",
    "💡 Use 'Apply Global' to enforce a single design criterion (e.g. max velocity) across every pipe at once.",
    "💡 Import/Export lets you edit the entire model in Excel and push the changes straight back in.",
    "💡 The Validation panel on the main menu updates live — aim for zero issues before generating reports.",
    "💡 Recent files are remembered between sessions — pick one from the list below to jump straight back in.",
    "💡 Drag & drop a .kdf file onto this window to load it without typing the full path.",
    "💡 Press Escape on any screen to go back — your inputs are preserved.",
    "💡 Model Info gives you a full breakdown: element counts, connectivity issues, and a searchable pipe list.",
    "💡 Config files (PMS, Stream data) are stored per-user — your settings survive pyKorf updates.",
    "💡 Stream data drives fluid properties like density and viscosity — keep it in sync with your HMB.",
    "💡 Saving often? Use the Quick Actions panel on the main menu — Save is just one click away.",
    "💡 Pipe schedules, materials and ratings set by PMS can still be overridden per-element afterwards.",
    "💡 Working on a large project? Batch reporting lets you process multiple .kdf files in one go.",
]


def get_random_tip() -> str:
    """Return a randomly chosen tip from the tips list.

    Returns:
        A tip string, ready to display in the UI.
    """
    return random.choice(TIPS)
