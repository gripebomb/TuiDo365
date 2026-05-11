"""Main TUI screen with three-pane layout."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header

from mtd.tui.widgets.list_sidebar import ListSidebar
from mtd.tui.widgets.status_bar import StatusBar
from mtd.tui.widgets.task_detail import TaskDetail
from mtd.tui.widgets.task_table import TaskTable


class MainScreen(Screen[None]):
    """Primary screen showing sidebar, task table, and detail panel."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Horizontal(id="main-container"):
                yield ListSidebar(id="sidebar")
                yield TaskTable(id="task-pane")
                yield TaskDetail(id="detail-pane")
            yield StatusBar(id="status-bar")
        yield Footer()
