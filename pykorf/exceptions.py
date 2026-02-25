"""
Custom exceptions for pyKorf.
"""


class KorfError(Exception):
    """Base exception for all pyKorf errors."""


class ParseError(KorfError):
    """Raised when a .kdf file cannot be parsed."""


class ElementNotFound(KorfError):
    """Raised when an element index does not exist in the model."""


class CaseError(KorfError):
    """Raised when an invalid case index or string is used."""


class AutomationError(KorfError):
    """Raised when KORF UI automation fails."""
