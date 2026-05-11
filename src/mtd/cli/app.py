"""Typer CLI application entrypoint."""

from __future__ import annotations

import typer

from mtd.cli.auth_commands import register_auth_commands
from mtd.cli.list_commands import register_list_commands
from mtd.cli.task_commands import register_task_commands
from mtd.cli.tui_command import register_tui_command

app = typer.Typer(
    help="Linux-first terminal client for Microsoft To Do",
    no_args_is_help=True,
)
register_auth_commands(app)
register_list_commands(app)
register_task_commands(app)
register_tui_command(app)
