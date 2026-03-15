"""Command-line entry point for pyKorf TUI."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta

TRIAL_START_DATE = datetime(2026, 3, 15)
TRIAL_DURATION_DAYS = 14
DEVELOPER_CONTACT = "Prasanna Palanivel"


def check_trial_expired() -> bool:
    """Check if the trial period has expired.

    Returns:
        True if trial has expired, False otherwise.
    """
    expiry_date = TRIAL_START_DATE + timedelta(days=TRIAL_DURATION_DAYS)
    return datetime.now() > expiry_date


def show_expired_message() -> None:
    """Display trial expired message and exit."""
    print("=" * 60)
    print("  pyKorf Trial Period Expired")
    print("=" * 60)
    print()
    print(f"  The trial period ({TRIAL_DURATION_DAYS} days) has ended.")
    print()
    print("  To continue using pyKorf, please contact the developer:")
    print(f"  {DEVELOPER_CONTACT}")
    print()
    print("=" * 60)


def main():
    """Launch the pyKorf TUI application."""
    parser = argparse.ArgumentParser(
        prog="pykorf",
        description="Enterprise Python toolkit for KORF hydraulic model files.",
    )
    parser.add_argument(
        "--trial",
        action="store_true",
        help="Run in trial mode (time-limited access)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (DEBUG log level, saves to {kdf-name}-debug.log)",
    )
    args = parser.parse_args()

    if args.trial:
        if check_trial_expired():
            show_expired_message()
            return
        days_left = (TRIAL_START_DATE + timedelta(days=TRIAL_DURATION_DAYS) - datetime.now()).days
        print(f"[Trial Mode] Days remaining: {max(0, days_left)}")
        print()

    from pykorf.use_case.tui import run_tui

    run_tui(debug=args.debug)


if __name__ == "__main__":
    main()
