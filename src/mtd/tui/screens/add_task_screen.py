"""Modal screen for adding a new task."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from mtd.domain.models import TaskImportance


class AddTaskScreen(ModalScreen[dict[str, object] | None]):
    """Modal dialog for creating a new task."""

    CSS = """
    AddTaskScreen {
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

    def __init__(self, list_name: str = "") -> None:
        super().__init__()
        self._list_name = list_name

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Static(f"Add Task — {self._list_name}", id="title")
            yield Static("", id="error")
            yield Label("Title:", classes="label")
            yield Input(placeholder="Task title", id="title-input")
            yield Label("Due date:", classes="label")
            yield Input(placeholder="YYYY-MM-DD (optional)", id="due-input")
            yield Label("Importance:", classes="label")
            yield Select(
                [(i.value, i.value) for i in TaskImportance],
                value=TaskImportance.NORMAL.value,
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

        result: dict[str, object] = {
            "title": title,
            "importance": importance_select.value,
        }

        due_str = due_input.value.strip()
        if due_str:
            try:
                datetime.strptime(due_str, "%Y-%m-%d")
                result["dueDateTime"] = {
                    "dateTime": f"{due_str}T00:00:00",
                    "timeZone": "UTC",
                }
            except ValueError:
                self.query_one("#error", Static).update(
                    "Due date must be YYYY-MM-DD"
                )
                return

        self.dismiss(result)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
