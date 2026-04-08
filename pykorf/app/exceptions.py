"""Use case specific exceptions."""

from __future__ import annotations

from pykorf.core.exceptions import KorfError


class UseCaseError(KorfError):
    """Base exception for use case module."""

    pass


class LineNumberParseError(UseCaseError):
    """Raised when line number cannot be parsed."""

    pass


class StreamNotFoundError(UseCaseError):
    """Raised when stream number not found in HMB data."""

    pass


class PmsLookupError(UseCaseError):
    """Raised when PMS lookup fails."""

    pass


class ValidationError(UseCaseError):
    """Raised when validation fails."""

    pass


class ExcelConversionError(UseCaseError):
    """Raised when Excel to JSON conversion fails."""

    pass


class ProcessError(UseCaseError):
    """Raised when KDF processing fails."""

    def __init__(self, message: str, pipe_name: str | None = None, file_path: str | None = None):
        super().__init__(message)
        self.pipe_name = pipe_name
        self.file_path = file_path
