"""Help overlay screen showing keyboard shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpScreen(ModalScreen[None]):
    """Modal overlay showing keyboard shortcuts."""

    CSS = """
    HelpScreen {
        align: center middle;
    }
    #dialog {
        width: 70;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    .section {
        text-style: bold;
        padding: 1 0 0 0;
    }
    .shortcut {
        padding: 0 1;
    }
    #footer {
        text-align: center;
        text-style: italic;
        padding: 1;
        color: $text-muted;
    }
    """

    CONTENT = """
[yellow bold]Navigation[/]
  [b]j/k[/b] or [b]↑/↓[/b]    Move up/down
  [b]g/G[/b]              Jump to top/bottom
  [b]Tab[/b]              Cycle focus between panels

[yellow bold]Actions[/]
  [b]r[/b]                Refresh data
  [b]a[/b]                Add new task
  [b]c[/b]                Toggle task complete
  [b]e[/b]                Edit task
  [b]d[/b]                Delete task

[yellow bold]Search & Filter[/]
  [b]/[/b]                Search tasks
  [b]1/2/3[/b]            Filter all/active/done
  [b]s[/b]                Change sort

[yellow bold]General[/]
  [b]i[/b]                Toggle detail pane
  [b]?[/b]                Show this help
  [b]q[/b]                Quit
"""

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            yield Static("Keyboard Shortcuts", id="title")
            yield Static(self.CONTENT, classes="shortcut")
            yield Static("Press any key to close", id="footer")

    def on_key(self, event) -> None:
        self.dismiss(None)

    def on_click(self) -> None:
        self.dismiss(None)
