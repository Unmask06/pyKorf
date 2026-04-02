"""Command-line entry point for pyKorf."""

from __future__ import annotations

import argparse
from datetime import date
from importlib.metadata import PackageNotFoundError, version

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from pykorf.license import validate_license_key
from pykorf.update import check_for_update, install_update
from pykorf.use_case.config import get_license_key, get_trial_start, set_trial_start

TRIAL_DURATION_DAYS = 30
DEVELOPER_CONTACT = "Prasanna Palanivel"

console = Console()


def get_version() -> str:
    """Get the package version dynamically."""
    try:
        return version("pykorf")
    except PackageNotFoundError:
        return "dev"


def show_splash() -> None:
    """Display pyKorf splash screen with branding."""
    console.clear()
    console.print()
    console.print()

    pkg_version = get_version()

    content = Text(justify="center")
    content.append("pyKorf", style="bold cyan")
    content.append(f"  v{pkg_version}\n", style="bold white")
    content.append("\n")
    content.append("Enterprise Hydraulic Modeling Toolkit\n", style="cyan")
    content.append("\n")
    content.append("KDF editor  ·  PMS/HMB automation  ·  Excel reporting", style="dim")

    console.print(
        Panel(
            Align.center(content),
            border_style="cyan",
            padding=(1, 6),
            width=70,
        ),
        justify="center",
    )
    console.print()


def _check_access() -> tuple[bool, int]:
    """Determine whether the user may run pyKorf and how many trial days remain.

    Checks the stored license key first. If no valid key is found, falls back
    to the trial period counted from the first-launch date stored in config.

    Returns:
        Tuple of ``(allowed, days_left)``.  ``days_left`` is ``-1`` when a
        valid license key is active (no expiry display needed), ``0`` when the
        trial has expired, or a positive integer for the remaining trial days.
    """
    key = get_license_key()
    if key:
        valid, _expiry, _err = validate_license_key(key)
        if valid:
            return True, -1

    trial_start_str = get_trial_start()
    if not trial_start_str:
        today_str = date.today().isoformat()
        set_trial_start(today_str)
        trial_start_str = today_str

    trial_start = date.fromisoformat(trial_start_str)
    days_elapsed = (date.today() - trial_start).days
    days_left = TRIAL_DURATION_DAYS - days_elapsed

    return days_left > 0, max(0, days_left)


def show_expired_message() -> None:
    """Display trial expired message."""
    console.clear()
    console.print()
    console.print()
    console.print()

    console.print(
        Panel(
            f"[red bold]Trial Period Expired[/red bold]\n\n"
            f"The [yellow]{TRIAL_DURATION_DAYS}-day[/yellow] trial has ended.\n\n"
            f"To continue using pyKorf, please enter a license key in:\n"
            f"[bold cyan]Preferences → License Key[/bold cyan]\n\n"
            f"Contact: [bold cyan]{DEVELOPER_CONTACT}[/bold cyan]",
            title="[red]⚠ Access Expired[/red]",
            border_style="red",
            padding=(1, 2),
        ),
        justify="center",
    )
    console.print()


def show_trial_info(days_left: int) -> None:
    """Display trial period information.

    Args:
        days_left: Number of days remaining in trial
    """
    if days_left <= 3:
        style = "red bold"
        urgency = "⚠"
    elif days_left <= 7:
        style = "yellow"
        urgency = "i"
    else:
        style = "green"
        urgency = "✓"

    console.print(
        Panel(
            f"[{style}]Trial Mode: {days_left} days remaining[/{style}]",
            title=f"{urgency} Trial Status",
            border_style="yellow" if days_left <= 7 else "green",
            padding=(0, 1),
        ),
        justify="center",
    )
    console.print()


def show_update_prompt(update_info: dict) -> None:
    """Display update notice and automatically install it.

    Args:
        update_info: Dict with 'latest_version', 'release_url', 'zipball_url',
            and optional 'sha256_url' keys.
    """
    latest_version = update_info["latest_version"]
    zipball_url = update_info.get("zipball_url", "")
    release_notes = update_info.get("release_notes", "")

    body = f"A newer version of pyKorf is available: [bold cyan]v{latest_version}[/bold cyan]\n"
    if release_notes:
        body += "\n[bold]What's new:[/bold]\n"
        body += f"[dim]{release_notes}[/dim]\n"
    body += "\n\nInstalling update automatically..."

    console.print(
        Panel(body, title="📦 Update Available", border_style="green", padding=(0, 1)),
        justify="center",
    )
    console.print()

    if not zipball_url:
        console.print("[yellow]No download URL available — please update manually.[/yellow]")
        console.print()
        return

    sha256_url = update_info.get("sha256_url")
    with console.status("[dim]Downloading and installing update...[/dim]", spinner="dots"):
        success, message = install_update(zipball_url, sha256_url=sha256_url)

    if success:
        console.print(
            Panel(
                f"[green]{message}[/green]",
                title="✅ Update Installed",
                border_style="green",
                padding=(0, 1),
            ),
            justify="center",
        )
    else:
        console.print(
            Panel(
                f"[red]{message}[/red]",
                title="❌ Update Failed",
                border_style="red",
                padding=(0, 1),
            ),
            justify="center",
        )

    console.print()


def main():
    """Launch the pyKorf web application."""
    parser = argparse.ArgumentParser(
        prog="pykorf",
        description="Enterprise Python toolkit for KORF hydraulic model files.",
    )
    parser.add_argument(
        "--trial",
        action="store_true",
        help="Enforce trial mode (time-limited access check)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the web UI server (default: 8000)",
    )
    args = parser.parse_args()

    show_splash()

    if args.trial:
        allowed, days_left = _check_access()
        if not allowed:
            show_expired_message()
            return
        if days_left >= 0:
            show_trial_info(days_left)

    pkg_version = get_version()
    if pkg_version != "dev":
        update_info = check_for_update(pkg_version)
        if update_info:
            show_update_prompt(update_info)

    from pykorf.use_case.web.app import run_server

    run_server(port=args.port)


if __name__ == "__main__":
    main()
