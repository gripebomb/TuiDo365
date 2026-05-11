"""CLI task-list commands.

Registers ``lists``, ``list-create``, ``list-rename``, and ``list-delete``
on the main Typer application.
"""

from __future__ import annotations

import json

import typer
from rich import print as rich_print
from rich.table import Table

from mtd.app.services.auth_service import AuthService
from mtd.app.services.list_service import ListService
from mtd.domain.errors import MtdError
from mtd.infra.auth.msal_client import MsalAuthClient
from mtd.infra.cache.store import CacheRepository
from mtd.infra.config.settings import MtdSettings
from mtd.infra.graph.client import GraphClient
from mtd.infra.graph.todo_api import TodoApiRepository


def _list_service() -> ListService:
    """Build a :class:`ListService` from current settings."""
    settings = MtdSettings()
    if not settings.is_configured():
        rich_print(
            "[red bold]Error:[/red bold] client_id is not configured.\n"
            "Set [code]MTD_CLIENT_ID[/code] or add [code]client_id[/code] to "
            "[code]~/.config/mtd/config.toml[/code]"
        )
        raise typer.Exit(1)
    auth_service = AuthService(MsalAuthClient(settings))
    graph_client = GraphClient(token_provider=auth_service.ensure_token)
    api = TodoApiRepository(graph_client)
    cache = CacheRepository()
    return ListService(api, cache)


def _format_age(seconds: float | None) -> str:
    if seconds is None:
        return ""
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    return f"{int(seconds / 3600)}h ago"


def register_list_commands(app: typer.Typer) -> None:
    """Add list commands to *app*."""

    @app.command(name="lists")
    def lists(
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
        offline: bool = typer.Option(False, "--offline", help="Read from cache"),
    ) -> None:
        """List all Microsoft To Do task lists."""
        service = _list_service()
        try:
            task_lists, freshness = service.get_lists(offline=offline)
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            raise typer.Exit(1) from exc

        if json_output:
            data = [lst.model_dump(mode="json") for lst in task_lists]
            rich_print(json.dumps(data, indent=2))
            return

        subtitle = ""
        if freshness.source == "cache":
            subtitle = f"[dim](cached {_format_age(freshness.age_seconds())})[/dim]"

        table = Table(title=f"Task Lists {subtitle}")
        table.add_column("Name", no_wrap=True)
        table.add_column("Built-in", justify="center")
        table.add_column("Shared", justify="center")

        for lst in task_lists:
            table.add_row(
                lst.display_name,
                "Yes" if lst.is_builtin else "No",
                "Yes" if lst.is_shared else "No",
            )

        rich_print(table)

    @app.command(name="list-create")
    def list_create(
        name: str = typer.Option(..., "--name", help="Name for the new list"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    ) -> None:
        """Create a new task list."""
        service = _list_service()
        try:
            task_list = service.create_list(name)
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            raise typer.Exit(1) from exc

        if json_output:
            rich_print(json.dumps(task_list.model_dump(mode="json"), indent=2))
            return

        rich_print(f"[green]Created list:[/green] {task_list.display_name}")

    @app.command(name="list-rename")
    def list_rename(
        name: str = typer.Option(..., "--name", help="Current list name"),
        new_name: str = typer.Option(..., "--new-name", help="New list name"),
    ) -> None:
        """Rename an existing task list."""
        service = _list_service()
        try:
            task_list = service.rename_list(name, new_name)
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            raise typer.Exit(1) from exc

        rich_print(f"[green]Renamed[/green] '{name}' → '{task_list.display_name}'")

    @app.command(name="list-delete")
    def list_delete(
        name: str = typer.Option(..., "--name", help="List name to delete"),
    ) -> None:
        """Delete a task list."""
        service = _list_service()
        try:
            service.delete_list(name)
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            raise typer.Exit(1) from exc

        rich_print(f"[green]Deleted list:[/green] '{name}'")
