"""License key generation and validation for pyKorf."""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import date

# Embedded secret — obfuscated in distribution builds.
# Changing this invalidates all previously issued keys.
_SECRET = b"pykorf_license_2026_v1"


def generate_license_key(expiry: date) -> str:
    """Generate a license key valid until the given expiry date.

    This is a developer utility. It is not required at runtime and
    should not be called from within the distributed application.

    Args:
        expiry: The date after which the key should be rejected.

    Returns:
        A hyphen-separated Base32 license key string.
    """
    payload = expiry.isoformat().encode()
    sig = hmac.new(_SECRET, payload, hashlib.sha256).digest()[:8]
    raw = base64.b32encode(payload + sig).decode().rstrip("=")
    return "-".join(raw[i : i + 5] for i in range(0, len(raw), 5))


def validate_license_key(key: str) -> tuple[bool, date | None, str]:
    """Validate a license key.

    Args:
        key: The license key string (hyphens optional, case-insensitive).

    Returns:
        A tuple of ``(is_valid, expiry_date, error_message)``.
        ``expiry_date`` is None when the key is malformed or has an invalid
        signature; it is set even for expired keys so callers can show the
        expiry date to the user.
    """
    try:
        raw = key.replace("-", "").upper()
        padding = (8 - len(raw) % 8) % 8
        decoded = base64.b32decode(raw + "=" * padding)
        payload, sig = decoded[:-8], decoded[-8:]
        expected_sig = hmac.new(_SECRET, payload, hashlib.sha256).digest()[:8]
        if not hmac.compare_digest(sig, expected_sig):
            return False, None, "Invalid license key"
        expiry = date.fromisoformat(payload.decode())
        if date.today() > expiry:
            return False, expiry, f"License expired on {expiry}"
        return True, expiry, ""
    except Exception:
        return False, None, "Malformed license key"
