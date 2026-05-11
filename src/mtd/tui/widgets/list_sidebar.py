"""Task list sidebar widget."""

from __future__ import annotations

from typing import Any

from textual.containers import Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from mtd.domain.models import TaskList


class ListSidebar(Vertical):
    """Left sidebar showing task lists."""

    DEFAULT_CSS = """
    ListSidebar {
        height: 100%;
        border: solid $primary;
    }
    #sidebar-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        height: auto;
    }
    OptionList {
        height: 1fr;
        border: none;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._option_list: OptionList | None = None

    def compose(self) -> None:  # type: ignore[misc,override]
        yield Static("Task Lists", id="sidebar-title")
        self._option_list = OptionList(id="list-options")
        yield self._option_list

    def on_mount(self) -> None:
        app = self.app
        app.watch(app, "lists", self._update_lists)
        app.watch(app, "selected_list", self._update_selection)
        app.watch(app, "error_message", self._update_error)

    def _update_lists(self, lists: list[TaskList]) -> None:
        if self._option_list is None:
            return
        self._option_list.clear_options()
        for task_list in lists:
            label = task_list.display_name
            if task_list.is_builtin:
                label += " ★"
            self._option_list.add_option(Option(label, id=task_list.id))

    def _update_selection(self, selected: TaskList | None) -> None:
        if self._option_list is None or selected is None:
            return
        for index, option in enumerate(self._option_list._options):
            if option.id == selected.id:
                self._option_list.highlighted = index
                return

    def _update_error(self, message: str) -> None:
        if message and self._option_list is not None:
            self._option_list.clear_options()
            self._option_list.add_option(Option(f"Error: {message}", disabled=True))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """When a list is selected, update the app's selected_list."""
        from mtd.tui.app import MtdApp

        app = self.app
        assert isinstance(app, MtdApp)
        option_id = event.option_id
        for task_list in app.lists:
            if task_list.id == option_id:
                app.selected_list = task_list
                return

    def on_key(self, event) -> None:
        """Vim-style navigation."""
        if event.key == "j":
            if self._option_list is not None:
                self._option_list.action_cursor_down()
        elif event.key == "k":
            if self._option_list is not None:
                self._option_list.action_cursor_up()
