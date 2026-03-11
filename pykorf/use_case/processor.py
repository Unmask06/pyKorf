"""Main PipedataProcessor for batch processing KDF files.

This module provides the PipedataProcessor class which processes KDF files
using PMS and HMB data to automatically populate pipe parameters.

Example:
    >>> from pykorf.use_case import PipedataProcessor
    >>>
    >>> processor = PipedataProcessor()
    >>> processor.load_pms("pms.json")
    >>> processor.load_hmb("hmb.json")
    >>> result = processor.process_kdf("model.kdf")
    >>> print(f"Processed {result.pipes_processed} pipes")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pykorf import Model
from pykorf.use_case.exceptions import (
    LineNumberParseError,
    PmsLookupError,
    ProcessError,
    StreamNotFoundError,
)
from pykorf.use_case.hmb import apply_hmb, load_hmb
from pykorf.use_case.line_number import (
    LineNumber,
    ValidationResult,
    parse_stream_from_notes,
)
from pykorf.use_case.pms import apply_pms, load_pms
from pykorf.use_case.settings import SettingsReader, UseCaseSettings

logger = logging.getLogger(__name__)


@dataclass
class PipeUpdateResult:
    """Result of processing a single pipe."""

    pipe_name: str
    success: bool
    line_number: str | None = None
    stream_no: str | None = None
    pms_schedule: str | None = None
    pms_material: str | None = None
    fluid_temp: float | None = None
    fluid_pres: float | None = None
    error: str | None = None


@dataclass
class ProcessResult:
    """Result of processing a KDF file."""

    file_path: Path
    pipes_processed: int = 0
    pipes_updated: int = 0
    pipe_results: list[PipeUpdateResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PipedataProcessor:
    """High-level processor for batch processing KDF files.

    This class processes KDF files by:
    1. Parsing line numbers from pipe NOTES fields
    2. Looking up PMS specifications from consolidated PMS data
    3. Looking up fluid properties from HMB data
    4. Updating pipe parameters in the KDF file via ``model.set_params()``

    Example:
        >>> processor = PipedataProcessor()
        >>> processor.load_pms("pms.json")
        >>> processor.load_hmb("hmb.json")
        >>> result = processor.process_kdf("model.kdf")
        >>> print(f"Processed {result.pipes_processed} pipes")
    """

    def __init__(self, settings: UseCaseSettings | Path | str | None = None):
        """Initialize PipedataProcessor.

        Args:
            settings: UseCaseSettings instance, or path to settings file, or None for defaults
        """
        if settings is None:
            self._settings = UseCaseSettings()
        elif isinstance(settings, (Path, str)):
            reader = SettingsReader()
            self._settings = reader.load(settings)
        else:
            self._settings = settings

        self._pms_source: Path | str | None = None
        self._hmb_source: Path | str | None = None
        self._pms_data: tuple[str, dict, dict] | None = None  # (material, pms_data, od_data)
        self._hmb_data: dict[str, dict[str, Any]] | None = None

    @property
    def settings(self) -> UseCaseSettings:
        """Get current settings."""
        return self._settings

    def load_pms(self, source: Path | str) -> None:
        """Load PMS data.

        Args:
            source: Path to PMS Excel or JSON file
        """
        self._pms_source = source
        material, pms_data, od_data = load_pms(source)
        self._pms_data = (material, pms_data, od_data)

    def load_hmb(self, source: Path | str) -> None:
        """Load HMB data.

        Args:
            source: Path to HMB Excel or JSON file
        """
        self._hmb_source = source
        self._hmb_data = load_hmb(source)

    def validate(self, notes_value: str) -> ValidationResult:
        """Validate line number format in NOTES field.

        Args:
            notes_value: The NOTES string to validate

        Returns:
            ValidationResult with validation status
        """
        return LineNumber.validate(notes_value, self._settings.notes_delimiter)

    def _process_pipe(self, pipe: Any) -> PipeUpdateResult:
        """Process a single pipe element.

        Args:
            pipe: Pipe element to process

        Returns:
            PipeUpdateResult with processing details
        """
        pipe_name = pipe.name
        notes = pipe.notes

        logger.info(f"Processing pipe: {pipe_name}")
        logger.debug(f"  NOTES field: {notes!r}")

        if not notes or not notes.strip():
            logger.warning(f"  Pipe {pipe_name}: NOTES field is empty, skipping")
            return PipeUpdateResult(
                pipe_name=pipe_name,
                success=False,
                error="NOTES field is empty",
            )

        result = PipeUpdateResult(pipe_name=pipe_name, success=False)

        line_number = LineNumber.parse(notes, self._settings.notes_delimiter)
        if line_number is None:
            logger.error(f"  Pipe {pipe_name}: Failed to parse line number from NOTES: {notes!r}")
            result.error = "Failed to parse line number from NOTES"
            return result

        logger.info(f"  Parsed line number: {line_number.raw_line_number}")
        logger.debug(f"    NPS: {line_number.nominal_pipe_size}")
        logger.debug(f"    Unit: {line_number.unit_number}")
        logger.debug(f"    Fluid: {line_number.fluid_code}")
        logger.debug(f"    Serial: {line_number.serial_number}")
        logger.debug(f"    PMS code: {line_number.pms_code}")

        result.line_number = line_number.raw_line_number

        stream_no = parse_stream_from_notes(notes, self._settings.notes_delimiter)
        if stream_no:
            logger.info(f"  Extracted stream number: {stream_no}")
            result.stream_no = stream_no
        else:
            logger.warning(f"  Pipe {pipe_name}: No stream number found in NOTES")

        # Apply PMS data if loaded
        if self._pms_data is not None:
            from pykorf.use_case.pms import lookup_schedule

            material, pms_data, od_data = self._pms_data
            pms_code = line_number.pms_code
            nps = line_number.nominal_pipe_size

            logger.info(f"  Looking up PMS: class={pms_code}, NPS={nps}")
            try:
                spec = lookup_schedule(pms_data, pms_code, float(nps))
                if "schedule" in spec:
                    result.pms_schedule = spec["schedule"]
                elif "wall_mm" in spec:
                    # Calculate ID from OD and wall thickness
                    wall_mm = spec["wall_mm"]
                    nps_float = float(nps)
                    od_mm = od_data.get(nps_float)
                    if od_mm is not None:
                        id_mm = od_mm - 2 * wall_mm
                        id_inch = id_mm / 25.4
                        result.pms_schedule = f"ID={id_inch:.3f}"
                    else:
                        result.pms_schedule = f"wall={wall_mm}mm"
                result.pms_material = material
                logger.info(f"  PMS lookup successful: SCH={result.pms_schedule}, MAT={material}")
            except PmsLookupError as e:
                logger.error(f"  PMS lookup failed: {e}")
                result.error = str(e)
                return result

        # Apply HMB data if loaded and stream number exists
        if self._hmb_data is not None and stream_no:
            from pykorf.use_case.hmb import lookup_stream

            logger.info(f"  Looking up HMB stream: {stream_no}")
            try:
                props = lookup_stream(self._hmb_data, stream_no)
                result.fluid_temp = props.get("temp")
                result.fluid_pres = props.get("pres")
                logger.info(
                    f"  HMB lookup successful: temp={result.fluid_temp}, pres={result.fluid_pres}"
                )
            except StreamNotFoundError as e:
                logger.error(f"  HMB lookup failed: {e}")
                result.error = str(e)
                return result

        result.success = True
        logger.info(f"  Successfully processed pipe {pipe_name}")
        return result

    def process_kdf(
        self,
        source: Model | Path | str,
        *,
        save: bool | None = None,
        save_path: Path | str | None = None,
    ) -> ProcessResult:
        """Process a single KDF file or in-memory Model.

        Args:
            source: Model instance, or path to KDF file.
            save: Whether to save after processing.  Defaults to ``True``
                when *source* is a file path, ``False`` when it is a Model.
            save_path: Optional output path. When ``None`` the model is saved
                back to its original location (file-path mode only).

        Returns:
            ProcessResult with processing details.

        Raises:
            ProcessError: If processing fails.
        """
        if isinstance(source, Model):
            model = source
            file_path = Path(save_path) if save_path else Path("<in-memory>")
            if save is None:
                save = False
        else:
            kdf_path = Path(source)
            if not kdf_path.exists():
                raise ProcessError(f"File not found: {kdf_path}")
            model = Model(kdf_path)
            file_path = kdf_path
            if save is None:
                save = True

        result = ProcessResult(file_path=file_path)

        # Apply PMS updates if loaded
        if self._pms_source is not None:
            try:
                apply_pms(
                    self._pms_source,
                    model,
                    delimiter=self._settings.notes_delimiter,
                    save=False,  # Processor handles saving
                )
            except (LineNumberParseError, PmsLookupError) as e:
                result.errors.append(f"PMS error: {e}")

        # Apply HMB updates if loaded
        if self._hmb_source is not None:
            try:
                apply_hmb(
                    self._hmb_source,
                    model,
                    delimiter=self._settings.notes_delimiter,
                    save=False,  # Processor handles saving
                )
            except StreamNotFoundError as e:
                result.errors.append(f"HMB error: {e}")

        # Build per-pipe results for reporting
        for idx in range(1, model.num_pipes + 1):
            pipe = model.pipes[idx]
            result.pipes_processed += 1

            try:
                pipe_result = self._process_pipe(pipe)
                result.pipe_results.append(pipe_result)

                if pipe_result.success:
                    result.pipes_updated += 1
                elif pipe_result.error and pipe_result.error not in result.errors:
                    result.errors.append(f"{pipe_result.pipe_name}: {pipe_result.error}")

            except Exception as e:
                error_msg = f"{pipe.name}: {e!s}"
                result.errors.append(error_msg)
                result.pipe_results.append(
                    PipeUpdateResult(
                        pipe_name=pipe.name,
                        success=False,
                        error=str(e),
                    )
                )

        if save:
            out = Path(save_path) if save_path else file_path
            if str(out) != "<in-memory>":
                model.save(out)

        return result

    def process_folder(
        self,
        folder_path: Path | str,
        pattern: str = "*.kdf",
    ) -> list[ProcessResult]:
        """Process all KDF files in a folder.

        Args:
            folder_path: Path to folder containing KDF files
            pattern: Glob pattern for matching KDF files

        Returns:
            List of ProcessResult for each processed file
        """
        folder_path = Path(folder_path)
        kdf_files = list(folder_path.glob(pattern))

        results: list[ProcessResult] = []

        for kdf_file in kdf_files:
            try:
                result = self.process_kdf(kdf_file)
                results.append(result)
            except ProcessError as e:
                results.append(
                    ProcessResult(
                        file_path=kdf_file,
                        errors=[str(e)],
                    )
                )

        return results
