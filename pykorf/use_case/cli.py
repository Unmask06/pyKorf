"""CLI entry point for pyKorf use case TUI."""

from __future__ import annotations


def main():
    """Entry point for the use case TUI CLI."""
    from pykorf.use_case.tui import run_tui

    run_tui()


if __name__ == "__main__":
    main()
