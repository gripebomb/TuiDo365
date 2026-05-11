"""CLI task commands.

Registers ``tasks``, ``add``, ``update``, ``done``, and ``delete`` on the
main Typer application.
"""

from __future__ import annotations

import json
from datetime import datetime

import typer
from rich import print as rich_print
from rich.table import Table

from mtd.app.services.auth_service import AuthService
from mtd.app.services.task_service import TaskService
from mtd.domain.errors import MtdError
from mtd.domain.models import TaskImportance
from mtd.infra.auth.msal_client import MsalAuthClient
from mtd.infra.cache.store import CacheRepository
from mtd.infra.config.settings import MtdSettings
from mtd.infra.graph.client import GraphClient
from mtd.infra.graph.todo_api import TodoApiRepository


def _task_service() -> TaskService:
    """Build a :class:`TaskService` from current settings."""
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
    return TaskService(api, cache)


def _format_age(seconds: float | None) -> str:
    if seconds is None:
        return ""
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    return f"{int(seconds / 3600)}h ago"


def register_task_commands(app: typer.Typer) -> None:
    """Add task commands to *app*."""

    @app.command(name="tasks")
    def tasks(
        list_name: str = typer.Option(..., "--list", help="Task list name"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
        offline: bool = typer.Option(False, "--offline", help="Read from cache"),
    ) -> None:
        """List tasks in a Microsoft To Do task list."""
        service = _task_service()
        try:
            task_list, task_items, freshness = service.get_tasks_by_list_name(
                list_name, offline=offline
            )
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            if exc.detail:
                rich_print(f"[dim]{exc.detail}[/dim]")
            raise typer.Exit(1) from exc

        if json_output:
            data = {
                "list": task_list.model_dump(mode="json"),
                "tasks": [t.model_dump(mode="json") for t in task_items],
            }
            rich_print(json.dumps(data, indent=2, default=str))
            return

        subtitle = ""
        if freshness.source == "cache":
            subtitle = f"[dim](cached {_format_age(freshness.age_seconds())})[/dim]"

        table = Table(title=f"Tasks – {task_list.display_name} {subtitle}")
        table.add_column("Status", justify="center", width=6)
        table.add_column("Title", no_wrap=False)
        table.add_column("Due", width=12)
        table.add_column("Importance", width=10)

        for task in task_items:
            status_icon = "[green]✓[/green]" if task.is_completed else " "
            due_str = task.due_at.strftime("%Y-%m-%d") if task.due_at else ""
            table.add_row(
                status_icon,
                task.title,
                due_str,
                task.importance.value,
            )

        rich_print(table)

    @app.command(name="add")
    def add(
        list_name: str = typer.Option(..., "--list", help="Task list name"),
        title: str = typer.Option(..., "--title", help="Task title"),
        due: str | None = typer.Option(None, "--due", help="Due date (YYYY-MM-DD)"),
        importance: str = typer.Option("normal", "--importance", help="low, normal, or high"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    ) -> None:
        """Add a new task to a list."""
        service = _task_service()
        try:
            due_at = _parse_date(due) if due else None
            importance_enum = TaskImportance(importance)
            task = service.create_task(list_name, title, due_at=due_at, importance=importance_enum)
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            if exc.detail:
                rich_print(f"[dim]{exc.detail}[/dim]")
            raise typer.Exit(1) from exc

        if json_output:
            rich_print(json.dumps(task.model_dump(mode="json"), indent=2, default=str))
            return

        rich_print(f"[green]Created task:[/green] {task.title}")
        if task.due_at:
            rich_print(f"  Due: {task.due_at.strftime('%Y-%m-%d')}")

    @app.command(name="done")
    def done(
        list_name: str = typer.Option(..., "--list", help="Task list name"),
        task_id: str = typer.Option(..., "--task-id", help="Task ID"),
    ) -> None:
        """Mark a task as completed."""
        service = _task_service()
        try:
            task = service.complete_task(list_name, task_id)
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            if exc.detail:
                rich_print(f"[dim]{exc.detail}[/dim]")
            raise typer.Exit(1) from exc

        rich_print(f"[green]Completed:[/green] {task.title}")

    @app.command(name="update")
    def update(
        list_name: str = typer.Option(..., "--list", help="Task list name"),
        task_id: str = typer.Option(..., "--task-id", help="Task ID"),
        title: str | None = typer.Option(None, "--title", help="New title"),
        due: str | None = typer.Option(None, "--due", help="New due date (YYYY-MM-DD)"),
        importance: str | None = typer.Option(None, "--importance", help="low, normal, or high"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    ) -> None:
        """Update an existing task."""
        service = _task_service()
        try:
            due_at = _parse_date(due) if due else None
            importance_enum = TaskImportance(importance) if importance else None
            task = service.update_task(
                list_name,
                task_id,
                title=title,
                due_at=due_at,
                importance=importance_enum,
            )
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            if exc.detail:
                rich_print(f"[dim]{exc.detail}[/dim]")
            raise typer.Exit(1) from exc

        if json_output:
            rich_print(json.dumps(task.model_dump(mode="json"), indent=2, default=str))
            return

        rich_print(f"[green]Updated task:[/green] {task.title}")

    @app.command(name="delete")
    def delete(
        list_name: str = typer.Option(..., "--list", help="Task list name"),
        task_id: str = typer.Option(..., "--task-id", help="Task ID"),
    ) -> None:
        """Delete a task."""
        service = _task_service()
        try:
            service.delete_task(list_name, task_id)
        except MtdError as exc:
            rich_print(f"[red bold]Error:[/red bold] {exc.message}")
            if exc.detail:
                rich_print(f"[dim]{exc.detail}[/dim]")
            raise typer.Exit(1) from exc

        rich_print("[green]Task deleted.[/green]")


def _parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD string into a datetime."""
    return datetime.strptime(date_str, "%Y-%m-%d")
