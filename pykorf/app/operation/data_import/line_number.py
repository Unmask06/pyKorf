"""Line number parsing and validation for KORF pipe elements.

This module provides the LineNumber dataclass which parses and validates
the standardized line number format used in pipe NOTES fields.

Format: N-AANNN-AAAA-NNN-AANANA-AAA-AA-XXX-XX

Position  Field                              Example
--------  ---------------------------------  --------
N         NOMINAL PIPE SIZE (INCHES)         6, 8, 10, 12
AANNN     UNIT NUMBER                        10U01, 20U02
AAAA      FLUID CODE                         WATR, STEA, COND
NNN       PIPING SERIAL NUMBER               001, 002
AANANA-AAA    PIPING CLASS                   BC1A1R-FHA (refer to PMS)
AA        INSULATION THICKNESS (mm)          50, 75, 100
XXX       TRACING TEMPERATURE (Deg C)        150, 200
XX        Reserved/Extension                 --
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import NamedTuple

MAX_LINE_NUMBER_LENGTH = 100

# Common fractions and their decimal equivalents
FRACTION_MAP = {
    "1/2": "0.5",
    "3/4": "0.75",
    "1/4": "0.25",
    "1/8": "0.125",
    "3/8": "0.375",
    "5/8": "0.625",
    "7/8": "0.875",
    "1/3": "0.333",
    "2/3": "0.667",
}

# Inverse map: decimal -> fraction (for DIA formatting)
DECIMAL_TO_FRACTION_MAP = {
    0.125: "1/8",
    0.25: "1/4",
    0.375: "3/8",
    0.5: "1/2",
    0.625: "5/8",
    0.75: "3/4",
    0.875: "7/8",
}


def format_nps(nps: float) -> str:
    """Format NPS value for KDF DIA parameter.

    Rules:
    - Values <= 1 inch: Use fractional representation if available (e.g., "3/4")
    - Whole numbers > 1: No decimal point (e.g., "2", "3")
    - Non-whole numbers > 1: Decimal without trailing zeros (e.g., "1.5")

    Args:
        nps: Nominal pipe size in inches.

    Returns:
        Formatted string for DIA parameter.

    Examples:
        >>> format_nps(0.75)
        '3/4'
        >>> format_nps(1.0)
        '1'
        >>> format_nps(1.5)
        '1.5'
        >>> format_nps(2.0)
        '2'
    """
    # Check for fractional representation (<= 1 inch)
    if nps <= 1.0 and nps in DECIMAL_TO_FRACTION_MAP:
        return DECIMAL_TO_FRACTION_MAP[nps]

    # Whole number: no decimal
    if nps == int(nps):
        return str(int(nps))

    # Non-whole number: decimal without trailing zeros
    return str(nps).rstrip("0").rstrip(".")


def _normalize_pipe_size(size_str: str) -> str:
    """Convert fractional pipe size to decimal.

    Examples:
        "1-1/2" -> "1.5"
        "3/4" -> "0.75"
        "2-1/2" -> "2.5"
        "6" -> "6"
    """
    if not size_str:
        return size_str

    # Check for whole-fraction combination (e.g., "1-1/2")
    if "-" in size_str:
        parts = size_str.split("-", 1)
        whole = parts[0]
        fraction = parts[1]
        if fraction in FRACTION_MAP:
            decimal_val = float(whole) + float(FRACTION_MAP[fraction])
            # Format without trailing .0 if it's a whole number
            if decimal_val == int(decimal_val):
                return str(int(decimal_val))
            return str(decimal_val).rstrip("0").rstrip(".")

    # Check for standalone fraction
    if size_str in FRACTION_MAP:
        return FRACTION_MAP[size_str]

    return size_str


class ValidationResult(NamedTuple):
    """Result of line number validation."""

    is_valid: bool
    error_message: str | None = None


@dataclass
class LineNumber:
    """Parsed line number with all components.

    Attributes:
        nominal_pipe_size: Pipe size in inches (N)
        unit_number: Unit identifier (AANNN)
        fluid_code: Fluid/medium code (AANAN - can contain digits)
        serial_number: Piping serial number (NNN)
        piping_class: PMS class code (AANANA-AAA)
        insulation_thickness: Insulation thickness in mm (AA)
        tracing_temp: Tracing temperature in °C (XXX), None if not present
    """

    nominal_pipe_size: float
    unit_number: str
    fluid_code: str
    serial_number: int
    piping_class: str
    coating_code: str
    insulation_thickness: int | None
    tracing_temp: int | None
    raw_line_number: str

    @property
    def pms_code(self) -> str:
        """Full PMS lookup key: piping class .

        Piping code 6 char + 3 char with hyphen separator (e.g., "BC1A1R-FHA" or "BC1A1R-FHA-FX2")
        """
        if self.coating_code:
            return f"{self.piping_class}-{self.coating_code}"
        return self.piping_class

    LINE_NUMBER_PATTERN = re.compile(
        r"^(\d+(?:\.\d+)?)-([A-Z0-9]+)-([A-Z0-9]+)-(\d+)-([A-Z0-9]+)(?:-([A-Z0-9]+))?(?:-([A-Z0-9]+))?(?:-([A-Z0-9]+))?(?:-([A-Z0-9]+))?$"
    )

    @classmethod
    def parse(cls, notes_value: str, delimiter: str = ";") -> LineNumber | None:
        r"""Parse line number from NOTES field value.

        Args:
            notes_value: The NOTES string (e.g., "14\"-CA020-BRL1-020-AP7A0F-FX2-N")
            delimiter: Delimiter separating line number from stream number

        Returns:
            LineNumber instance if parsing succeeds, None otherwise
        """
        if not notes_value:
            return None

        notes_value = notes_value.strip()
        if len(notes_value) > MAX_LINE_NUMBER_LENGTH:
            return None

        if delimiter in notes_value:
            line_part = notes_value.split(delimiter)[0]
        else:
            line_part = notes_value

        line_part = line_part.replace('"', "").replace(" ", "")

        if len(line_part) > MAX_LINE_NUMBER_LENGTH:
            return None

        # Normalize fractional pipe sizes (e.g., "1-1/2-EV180..." -> "1.5-EV180...")
        # Match patterns like "1-1/2" or "3/4" at the start of the line number
        line_part = re.sub(
            r"^(\d+)-(\d/\d)|^(\d/\d)", lambda m: _normalize_pipe_size(m.group(0)), line_part
        )

        match = cls.LINE_NUMBER_PATTERN.match(line_part)
        if not match:
            return None

        groups = match.groups()

        nominal_pipe_size = float(groups[0])
        unit_number = groups[1]
        fluid_code = groups[2]
        serial_number = int(groups[3])
        piping_class = groups[4]
        coating_code = groups[5] if groups[5] else ""

        def to_int(val):
            if val and val.isdigit():
                return int(val)
            return None

        insulation_thickness = to_int(groups[6])
        tracing_temp = to_int(groups[7])

        return cls(
            nominal_pipe_size=nominal_pipe_size,
            unit_number=unit_number,
            fluid_code=fluid_code,
            serial_number=serial_number,
            piping_class=piping_class,
            coating_code=coating_code,
            insulation_thickness=insulation_thickness,
            tracing_temp=tracing_temp,
            raw_line_number=line_part,
        )

    @classmethod
    def validate(cls, notes_value: str, delimiter: str = ";") -> ValidationResult:
        """Validate line number format without full parsing.

        Args:
            notes_value: The NOTES string to validate
            delimiter: Delimiter used in NOTES field

        Returns:
            ValidationResult with is_valid=True if format is correct
        """
        if not notes_value or not notes_value.strip():
            return ValidationResult(False, "NOTES field is empty")

        notes_value = notes_value.strip()
        if len(notes_value) > MAX_LINE_NUMBER_LENGTH:
            return ValidationResult(
                False, f"NOTES value exceeds maximum length ({MAX_LINE_NUMBER_LENGTH})"
            )

        if delimiter in notes_value:
            line_part = notes_value.split(delimiter)[0]
        else:
            line_part = notes_value

        if len(line_part) > MAX_LINE_NUMBER_LENGTH:
            return ValidationResult(
                False, f"Line number exceeds maximum length ({MAX_LINE_NUMBER_LENGTH})"
            )

        if not cls.LINE_NUMBER_PATTERN.match(line_part):
            return ValidationResult(False, f"Invalid line number format: {line_part}")

        return ValidationResult(True)


def parse_stream_from_notes(notes_value: str, delimiter: str = ";") -> str | None:
    r"""Extract stream number from NOTES field.

    Args:
        notes_value: The NOTES string (e.g., "14\"-CA020-BRL1-020-AP7A0F-FX2-N;S-101;")
        delimiter: Delimiter separating components

    Returns:
        Stream number (e.g., "S-101") if present, None otherwise
    """
    if not notes_value or not notes_value.strip():
        return None

    parts = notes_value.strip().split(delimiter)
    if len(parts) >= 2:
        stream = parts[1].strip().replace('"', "")
        if stream:
            return stream

    return None


def extract_fluid_seq_from_notes(notes_value: str, delimiter: str = ";") -> str | None:
    r"""Extract fluid code and serial number from NOTES field.

    Args:
        notes_value: The NOTES string (e.g., "3\"-EV170-VCL17-806-BC1A1B-FMB-P;")
        delimiter: Delimiter separating line number from stream number

    Returns:
        Fluid code and serial number (e.g., "VCL17-806") if present, None otherwise
    """
    if not notes_value or not notes_value.strip():
        return None

    notes_value = notes_value.strip()
    if delimiter in notes_value:
        line_part = notes_value.split(delimiter)[0]
    else:
        line_part = notes_value

    line_part = line_part.replace('"', "").replace(" ", "")

    # Normalize fractional pipe sizes (e.g., "1-1/2-EV180..." -> "1.5-EV180...")
    line_part = re.sub(
        r"^(\d+)-(\d/\d)|^(\d/\d)", lambda m: _normalize_pipe_size(m.group(0)), line_part
    )

    match = LineNumber.LINE_NUMBER_PATTERN.match(line_part)
    if not match:
        return None

    groups = match.groups()
    fluid_code = groups[2]
    serial_number = groups[3]

    return f"{fluid_code}-{serial_number}"
