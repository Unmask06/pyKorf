"""
Custom exceptions for pyKorf with structured error context.

This module provides a comprehensive exception hierarchy for all pyKorf errors,
with support for structured error context, error chaining, and user-friendly
error messages.

Example:
    >>> from pykorf.exceptions import ElementNotFound, ErrorContext
    >>> raise ElementNotFound(
    ...     "Element 'P1' not found",
    ...     context=ErrorContext(element_type="PUMP", element_name="P1")
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ErrorContext:
    """Structured context information for pyKorf errors.
    
    Attributes:
        element_type: The KDF element type (e.g., 'PIPE', 'PUMP').
        element_name: The name/tag of the element.
        element_index: The numeric index of the element.
        parameter: The parameter that caused the error.
        file_path: The path to the file being processed.
        line_number: The line number in the file (if applicable).
        additional_data: Any additional context-specific data.
    """
    element_type: str | None = None
    element_name: str | None = None
    element_index: int | None = None
    parameter: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    additional_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to a dictionary."""
        return {
            k: v for k, v in {
                "element_type": self.element_type,
                "element_name": self.element_name,
                "element_index": self.element_index,
                "parameter": self.parameter,
                "file_path": self.file_path,
                "line_number": self.line_number,
                **self.additional_data,
            }.items() if v is not None
        }


class KorfError(Exception):
    """Base exception for all pyKorf errors.
    
    Attributes:
        message: The error message.
        context: Structured error context.
        suggestion: Optional suggestion for resolving the error.
    """
    
    def __init__(
        self,
        message: str,
        *,
        context: ErrorContext | None = None,
        suggestion: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.suggestion = suggestion

    def __str__(self) -> str:
        parts = [self.message]
        ctx_dict = self.context.to_dict()
        if ctx_dict:
            parts.append(f"Context: {ctx_dict}")
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return " | ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to a dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context.to_dict(),
            "suggestion": self.suggestion,
        }


class ParseError(KorfError):
    """Raised when a .kdf file cannot be parsed.
    
    This includes syntax errors, encoding issues, malformed records,
    and version incompatibility.
    """
    pass


class ElementNotFound(KorfError):
    """Raised when an element is not found in the model."""
    
    def __init__(
        self,
        name: str,
        *,
        available_names: list[str] | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        message = f"No element named {name!r} in model"
        suggestion = None
        if available_names:
            # Find similar names using simple substring matching
            similar = [n for n in available_names if name.lower() in n.lower() or n.lower() in name.lower()]
            if similar:
                suggestion = f"Did you mean: {', '.join(similar[:3])}?"
        super().__init__(message, context=context, suggestion=suggestion)
        self.name = name
        self.available_names = available_names


class ElementAlreadyExists(KorfError):
    """Raised when attempting to create an element with a duplicate name."""
    
    def __init__(self, name: str, existing_type: str | None = None) -> None:
        message = f"Element {name!r} already exists"
        if existing_type:
            message += f" (type: {existing_type})"
        super().__init__(
            message,
            context=ErrorContext(element_name=name, element_type=existing_type),
            suggestion="Use a different name or delete the existing element first.",
        )
        self.name = name
        self.existing_type = existing_type


class CaseError(KorfError):
    """Raised when an invalid case index or string is used."""
    pass


class AutomationError(KorfError):
    """Raised when KORF UI automation fails."""
    pass


class ValidationError(KorfError):
    """Raised when KDF model validation fails.
    
    Contains a list of validation issues.
    """
    
    def __init__(
        self,
        issues: list[str],
        *,
        file_path: str | None = None,
    ) -> None:
        message = f"Validation failed with {len(issues)} issue(s)"
        super().__init__(
            message,
            context=ErrorContext(file_path=file_path),
            suggestion="Run model.validate() to see all issues.",
        )
        self.issues = issues

    def __str__(self) -> str:
        base = super().__str__()
        issues_str = "\n".join(f"  - {issue}" for issue in self.issues[:5])
        if len(self.issues) > 5:
            issues_str += f"\n  ... and {len(self.issues) - 5} more issues"
        return f"{base}\nIssues:\n{issues_str}"


class ConnectivityError(KorfError):
    """Raised when an element connection operation is invalid."""
    pass


class LayoutError(KorfError):
    """Raised when an element layout or positioning issue is detected."""
    pass


class VersionError(KorfError):
    """Raised when a KDF version is not supported or incompatible."""
    
    def __init__(
        self,
        version: str,
        supported_versions: list[str] | None = None,
    ) -> None:
        message = f"Unsupported KDF version: {version!r}"
        suggestion = None
        if supported_versions:
            suggestion = f"Supported versions: {', '.join(supported_versions)}"
        super().__init__(message, suggestion=suggestion)
        self.version = version
        self.supported_versions = supported_versions


class ParameterError(KorfError):
    """Raised when a parameter operation fails."""
    pass


class ExportError(KorfError):
    """Raised when exporting model data fails."""
    pass


class ImportError(KorfError):
    """Raised when importing model data fails."""
    pass


__all__ = [
    "ErrorContext",
    "KorfError",
    "ParseError",
    "ElementNotFound",
    "ElementAlreadyExists",
    "CaseError",
    "AutomationError",
    "ValidationError",
    "ConnectivityError",
    "LayoutError",
    "VersionError",
    "ParameterError",
    "ExportError",
    "ImportError",
]
