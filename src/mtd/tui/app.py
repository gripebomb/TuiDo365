"""Main Textual TUI application for TuiDo365."""

from __future__ import annotations

from textual.app import App
from textual.reactive import reactive

from mtd.app.services.auth_service import AuthService
from mtd.app.services.list_service import ListService
from mtd.app.services.task_service import TaskService
from mtd.domain.errors import MtdError
from mtd.domain.models import Task, TaskList
from mtd.infra.auth.msal_client import MsalAuthClient
from mtd.infra.cache.store import CacheRepository
from mtd.infra.config.settings import MtdSettings
from mtd.infra.graph.client import GraphClient
from mtd.infra.graph.todo_api import TodoApiRepository
from mtd.tui.screens.main_screen import MainScreen


class MtdApp(App[None]):
    """Textual TUI for Microsoft To Do."""

    CSS = """
    Screen { align: center middle; }
    #main-container { layout: horizontal; height: 100%; }
    #sidebar { width: 25%; height: 100%; border: solid $primary; }
    #task-pane { width: 45%; height: 100%; border: solid $primary; }
    #detail-pane { width: 30%; height: 100%; border: solid $primary; }
    .panel-title { text-align: center; text-style: bold; padding: 1; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("tab", "cycle_focus", "Focus"),
    ]

    lists: reactive[list[TaskList]] = reactive(list)
    tasks: reactive[list[Task]] = reactive(list)
    selected_list: reactive[TaskList | None] = reactive(None)
    selected_task: reactive[Task | None] = reactive(None)
    error_message: reactive[str] = reactive("")

    def __init__(self, settings: MtdSettings | None = None) -> None:
        super().__init__()
        self._settings = settings or MtdSettings()
        self._auth_service: AuthService | None = None
        self._list_service: ListService | None = None
        self._task_service: TaskService | None = None

    def _init_services(self) -> None:
        if not self._settings.is_configured():
            self.error_message = (
                "client_id not configured. Set MTD_CLIENT_ID or add "
                "client_id to ~/.config/mtd/config.toml"
            )
            return
        self._auth_service = AuthService(MsalAuthClient(self._settings))
        graph_client = GraphClient(token_provider=self._auth_service.ensure_token)
        api = TodoApiRepository(graph_client)
        cache = CacheRepository()
        self._list_service = ListService(api, cache)
        self._task_service = TaskService(api, cache)

    def on_mount(self) -> None:
        self._init_services()
        self.push_screen(MainScreen())
        self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh lists and tasks from Graph."""
        if self._list_service is None:
            return
        try:
            lists, _ = self._list_service.get_lists()
            self.lists = lists
            self.error_message = ""
        except MtdError as exc:
            self.error_message = exc.message

    def refresh_tasks(self) -> None:
        """Load tasks for the currently selected list."""
        if self._task_service is None or self.selected_list is None:
            self.tasks = []
            return
        try:
            _, tasks, _ = self._task_service.get_tasks_by_list_name(self.selected_list.display_name)
            self.tasks = tasks
            self.error_message = ""
        except MtdError as exc:
            self.error_message = exc.message
            self.tasks = []

    def watch_selected_list(self, task_list: TaskList | None) -> None:
        """When the selected list changes, reload tasks."""
        self.selected_task = None
        self.refresh_tasks()
