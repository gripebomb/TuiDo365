"""CLI authentication commands.

Registers ``login`` and ``logout`` on the main Typer application so they
appear as ``mtd login`` and ``mtd logout``.
"""

from __future__ import annotations

import typer
from rich import print as rich_print

from mtd.app.services.auth_service import AuthService
from mtd.domain.errors import MtdError
from mtd.infra.auth.msal_client import MsalAuthClient
from mtd.infra.config.settings import MtdSettings


def _auth_service() -> AuthService:
    """Build an :class:`AuthService` from current settings.

    Exits with a friendly message when the app is not configured.
    """
    settings = MtdSettings()
    if not settings.is_configured():
        rich_print(
            "[red bold]Error:[/red bold] client_id is not configured.\n"
            "Set [code]MTD_CLIENT_ID[/code] or add [code]client_id[/code] to "
            "[code]~/.config/mtd/config.toml[/code]"
        )
        raise typer.Exit(1)
    return AuthService(MsalAuthClient(settings))


def register_auth_commands(app: typer.Typer) -> None:
    """Add ``login`` and ``logout`` commands to *app*."""

    @app.command()
    def login() -> None:
        """Authenticate with Microsoft To Do using device-code flow."""
        service = _auth_service()
        try:
            info = service.initiate_login()
            rich_print(info.message)
            result = service.complete_login(info.flow)
            username = result.account_username or "unknown user"
            rich_print(f"[green]Logged in as {username}.[/green]")
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            raise typer.Exit(1) from exc

    @app.command()
    def logout() -> None:
        """Remove saved credentials."""
        service = _auth_service()
        try:
            service.logout()
            rich_print("[green]Logged out.[/green]")
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            raise typer.Exit(1) from exc
