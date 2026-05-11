"""Status bar widget showing sync state, counts, and errors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from textual.containers import Horizontal
from textual.widgets import Static


class StatusBar(Horizontal):
    """Footer bar showing sync status, counts, and messages."""

    DEFAULT_CSS = """
    StatusBar {
        height: auto;
        border: solid $primary;
        padding: 0 1;
    }
    #status-left {
        width: 60%;
        content-align-vertical: middle;
    }
    #status-right {
        width: 40%;
        content-align: right middle;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._left: Static | None = None
        self._right: Static | None = None
        self._last_sync: datetime | None = None
        self._list_count = 0
        self._task_count = 0
        self._offline = False
        self._error = ""

    def compose(self) -> None:  # type: ignore[misc,override]
        self._left = Static("Ready", id="status-left")
        self._right = Static("", id="status-right")
        yield self._left
        yield self._right

    def on_mount(self) -> None:
        app = self.app
        app.watch(app, "lists", self._on_lists_change)
        app.watch(app, "tasks", self._on_tasks_change)
        app.watch(app, "error_message", self._on_error_change)

    def _on_lists_change(self, lists: list[Any]) -> None:
        self._list_count = len(lists)
        self._last_sync = datetime.now(timezone.utc)
        self._offline = False
        self._update()

    def _on_tasks_change(self, tasks: list[Any]) -> None:
        self._task_count = len(tasks)
        self._update()

    def _on_error_change(self, message: str) -> None:
        if message:
            self._error = message
        else:
            self._error = ""
        self._update()

    def _update(self) -> None:
        if self._left is None or self._right is None:
            return

        if self._error:
            self._left.update(f"[b red]Error:[/b red] {self._error}")
            self._right.update("")
            return

        sync_text = ""
        if self._last_sync:
            ago = self._relative_time(self._last_sync)
            sync_text = f"Synced {ago}"
        if self._offline:
            sync_text = "[yellow]Offline[/yellow]"

        left_text = sync_text
        if self._list_count or self._task_count:
            counts = []
            if self._list_count:
                counts.append(f"{self._list_count} lists")
            if self._task_count:
                counts.append(f"{self._task_count} tasks")
            if counts:
                left_text += f"  |  {' | '.join(counts)}"

        self._left.update(left_text)
        self._right.update("Press [b]?[/b] for help")

    @staticmethod
    def _relative_time(when: datetime) -> str:
        now = datetime.now(timezone.utc)
        delta = now - when
        seconds = int(delta.total_seconds())
        if seconds < 5:
            return "just now"
        if seconds < 60:
            return f"{seconds}s ago"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        return f"{hours}h ago"
