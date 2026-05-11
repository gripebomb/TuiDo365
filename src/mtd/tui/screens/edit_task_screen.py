"""Modal screen for editing a task."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from mtd.domain.models import Task, TaskImportance


class EditTaskScreen(ModalScreen[dict[str, object] | None]):
    """Modal dialog for editing an existing task."""

    CSS = """
    EditTaskScreen {
        align: center middle;
    }
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        padding: 0 1;
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
    }
    #title {
        column-span: 2;
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    #error {
        column-span: 2;
        color: $error;
        text-align: center;
        height: auto;
    }
    .label {
        content-align-vertical: middle;
    }
    Button {
        width: 100%;
    }
    """

    def __init__(self, task: Task) -> None:
        super().__init__()
        self._task_data = task

    def compose(self) -> ComposeResult:
        due_str = ""
        if self._task_data.due_at:
            due_str = self._task_data.due_at.strftime("%Y-%m-%d")

        with Grid(id="dialog"):
            yield Static("Edit Task", id="title")
            yield Static("", id="error")
            yield Label("Title:", classes="label")
            yield Input(value=self._task_data.title, id="title-input")
            yield Label("Due date:", classes="label")
            yield Input(value=due_str, placeholder="YYYY-MM-DD (optional)", id="due-input")
            yield Label("Importance:", classes="label")
            yield Select(
                [(i.value, i.value) for i in TaskImportance],
                value=self._task_data.importance.value,
                id="importance-select",
            )
            yield Button("Save", variant="primary", id="save")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return

        title_input = self.query_one("#title-input", Input)
        due_input = self.query_one("#due-input", Input)
        importance_select = self.query_one("#importance-select", Select)

        title = title_input.value.strip()
        if not title:
            self.query_one("#error", Static).update("Title is required")
            return

        result: dict[str, object] = {}

        if title != self._task_data.title:
            result["title"] = title

        new_importance = str(importance_select.value)
        if new_importance != self._task_data.importance.value:
            result["importance"] = new_importance

        due_str = due_input.value.strip()
        if due_str:
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
                new_due = {
                    "dateTime": f"{due_str}T00:00:00",
                    "timeZone": "UTC",
                }
                result["dueDateTime"] = new_due
            except ValueError:
                self.query_one("#error", Static).update(
                    "Due date must be YYYY-MM-DD"
                )
                return

        self.dismiss(result)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
