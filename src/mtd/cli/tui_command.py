"""CLI command to launch the TUI."""

from __future__ import annotations

import typer
from rich import print as rich_print

from mtd.infra.config.settings import MtdSettings
from mtd.tui.app import MtdApp


def register_tui_command(app: typer.Typer) -> None:
    """Add ``tui`` command to *app*."""

    @app.command(name="tui")
    def tui() -> None:
        """Launch the interactive terminal UI."""
        settings = MtdSettings()
        if not settings.is_configured():
            rich_print(
                "[red bold]Error:[/red bold] client_id is not configured.\n"
                "Set [code]MTD_CLIENT_ID[/code] or add [code]client_id[/code] to "
                "[code]~/.config/mtd/config.toml[/code]"
            )
            raise typer.Exit(1)
        MtdApp(settings=settings).run()
