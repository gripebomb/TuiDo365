"""Task table widget."""

from __future__ import annotations

from typing import Any

from textual.containers import Vertical
from textual.widgets import DataTable, Static

from mtd.domain.models import Task


class TaskTable(Vertical):
    """Central pane showing tasks in a table."""

    DEFAULT_CSS = """
    TaskTable {
        height: 100%;
        border: solid $primary;
    }
    #table-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        height: auto;
    }
    DataTable {
        height: 1fr;
        border: none;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._table: DataTable | None = None
        self._task_map: dict[Any, Task] = {}
        self._all_tasks: list[Task] = []

    def compose(self) -> None:  # type: ignore[misc,override]
        yield Static("Tasks", id="table-title")
        self._table = DataTable(id="task-data-table")
        yield self._table

    def on_mount(self) -> None:
        app = self.app
        app.watch(app, "tasks", self._update_tasks)
        app.watch(app, "selected_task", self._update_selection)
        app.watch(app, "error_message", self._update_error)
        if self._table is not None:
            self._table.cursor_type = "row"
            self._table.add_columns("Status", "Title", "Due", "Importance")

    def _update_tasks(self, tasks: list[Task]) -> None:
        self._all_tasks = tasks
        self._display_filtered(tasks)

    def _display_filtered(self, tasks: list[Task]) -> None:
        if self._table is None:
            return
        self._table.clear()
        self._task_map.clear()
        for task in tasks:
            row_key = self._table.add_row(
                "✓" if task.is_completed else " ",
                task.title,
                task.due_at.strftime("%Y-%m-%d") if task.due_at else "",
                task.importance.value,
            )
            self._task_map[row_key] = task

    def _update_selection(self, selected: Task | None) -> None:
        if self._table is None or selected is None:
            return
        for row_key, task in self._task_map.items():
            if task.id == selected.id:
                self._table.move_cursor(row=self._table.get_row_index(row_key))
                return

    def _update_error(self, message: str) -> None:
        if message and self._table is not None:
            self._table.clear()
            self._task_map.clear()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """When a task row is selected, update the app's selected_task."""
        from mtd.tui.app import MtdApp

        task = self._task_map.get(event.row_key)
        if task is not None:
            app = self.app
            assert isinstance(app, MtdApp)
            app.selected_task = task

    def on_key(self, event) -> None:
        """Vim-style navigation."""
        if self._table is None:
            return
        if event.key == "j":
            self._table.action_cursor_down()
        elif event.key == "k":
            self._table.action_cursor_up()
        elif event.key == "g":
            self._table.move_cursor(row=0)
        elif event.key == "G":
            self._table.move_cursor(row=self._table.row_count - 1)
