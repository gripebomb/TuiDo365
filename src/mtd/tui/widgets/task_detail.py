"""Task detail panel widget."""

from __future__ import annotations

from typing import Any

from textual.containers import Vertical
from textual.widgets import Static

from mtd.domain.models import Task


class TaskDetail(Vertical):
    """Right panel showing details of the selected task."""

    DEFAULT_CSS = """
    TaskDetail {
        height: 100%;
        border: solid $primary;
    }
    #detail-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        height: auto;
    }
    #detail-content {
        padding: 1;
        height: 1fr;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._content: Static | None = None

    def compose(self) -> None:  # type: ignore[misc,override]
        yield Static("Task Detail", id="detail-title")
        self._content = Static("Select a task to view details.", id="detail-content")
        yield self._content

    def on_mount(self) -> None:
        app = self.app
        app.watch(app, "selected_task", self._update_task)

    def _update_task(self, task: Task | None) -> None:
        if self._content is None:
            return
        if task is None:
            self._content.update("Select a task to view details.")
            return

        lines: list[str] = [
            f"[b]Title:[/b] {task.title}",
            f"[b]Status:[/b] {task.status.value}",
            f"[b]Importance:[/b] {task.importance.value}",
        ]
        if task.due_at:
            lines.append(f"[b]Due:[/b] {task.due_at.strftime('%Y-%m-%d')}")
        if task.completed_at:
            lines.append(f"[b]Completed:[/b] {task.completed_at.strftime('%Y-%m-%d')}")
        if task.reminder_at:
            lines.append(f"[b]Reminder:[/b] {task.reminder_at.strftime('%Y-%m-%d')}")
        if task.body and task.body.content:
            lines.append(f"[b]Notes:[/b] {task.body.content}")
        if task.categories:
            lines.append(f"[b]Categories:[/b] {', '.join(task.categories)}")
        lines.append(f"[dim]ID: {task.id}[/dim]")

        self._content.update("\n".join(lines))
