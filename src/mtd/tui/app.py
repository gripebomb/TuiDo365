"""Main Textual TUI application for TuiDo365."""

from __future__ import annotations

from datetime import UTC, datetime

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
from mtd.tui.screens.add_task_screen import AddTaskScreen
from mtd.tui.screens.edit_task_screen import EditTaskScreen
from mtd.tui.screens.help_screen import HelpScreen
from mtd.tui.screens.main_screen import MainScreen
from mtd.tui.widgets.task_table import TaskTable


class MtdApp(App[None]):
    """Textual TUI for Microsoft To Do."""

    CSS = """
    Screen { align: center middle; }
    #main-container { layout: horizontal; height: 1fr; }
    #sidebar { width: 25%; height: 100%; border: solid $primary; }
    #task-pane { width: 45%; height: 100%; border: solid $primary; }
    #detail-pane { width: 30%; height: 100%; border: solid $primary; }
    .panel-title { text-align: center; text-style: bold; padding: 1; }
    #status-bar { height: auto; dock: bottom; }
    """

    def action_cycle_focus(self) -> None:
        """Cycle focus between panels."""
        focused = self.focused
        if focused is None:
            self.set_focus(self.query_one("#sidebar", ListSidebar))
            return
        if focused.parent and focused.parent.id == "sidebar":
            self.set_focus(self.query_one("#task-pane", TaskTable))
        elif focused.parent and focused.parent.id == "task-pane":
            self.set_focus(self.query_one("#detail-pane", TaskDetail))
        else:
            self.set_focus(self.query_one("#sidebar", ListSidebar))

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("tab", "cycle_focus", "Focus"),
        ("c", "toggle_complete", "Complete"),
        ("a", "add_task", "Add"),
        ("d", "delete_task", "Delete"),
        ("e", "edit_task", "Edit"),
        ("slash", "search", "Search"),
        ("s", "sort_tasks", "Sort"),
        ("1", "filter_all", "All"),
        ("2", "filter_active", "Active"),
        ("3", "filter_completed", "Done"),
        ("question_mark", "help", "Help"),
        ("i", "toggle_detail", "Info"),
    ]

    lists: reactive[list[TaskList]] = reactive(list)
    tasks: reactive[list[Task]] = reactive(list)
    selected_list: reactive[TaskList | None] = reactive(None)
    selected_task: reactive[Task | None] = reactive(None)
    error_message: reactive[str] = reactive("")
    search_query: reactive[str] = reactive("")
    task_filter: reactive[str] = reactive("all")  # all, active, completed
    sort_mode: reactive[str] = reactive("due")  # due, importance, title, created

    def __init__(self, settings: MtdSettings | None = None) -> None:
        import os
        super().__init__()
        self._settings = settings or MtdSettings()
        self._auth_service: AuthService | None = None
        self._list_service: ListService | None = None
        self._task_service: TaskService | None = None
        if os.environ.get("NO_COLOR"):
            self.console._color_system = None

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

    def watch_search_query(self, query: str) -> None:
        """When search query changes, refresh display."""
        self._apply_task_display()

    def watch_task_filter(self, filter_val: str) -> None:
        """When filter changes, refresh display."""
        self._apply_task_display()

    def watch_sort_mode(self, mode: str) -> None:
        """When sort mode changes, refresh display."""
        self._apply_task_display()

    def watch_selected_list(self, task_list: TaskList | None) -> None:
        """When the selected list changes, reload tasks."""
        self.selected_task = None
        self.refresh_tasks()

    def action_toggle_complete(self) -> None:
        """Toggle completion status of selected task."""
        if self._task_service is None or self.selected_task is None or self.selected_list is None:
            return
        task = self.selected_task
        try:
            if task.status.value == "notStarted":
                self._task_service.complete_task(
                    self.selected_list.display_name, task.id
                )
            else:
                # Mark as not started using the API directly
                task_list = self._task_service._resolve_list(
                    self.selected_list.display_name
                )
                self._task_service._api.update_task(
                    task_list.id, task.id, {"status": "notStarted"}
                )
            self.refresh_tasks()
            self.error_message = "Task updated"
        except MtdError as exc:
            self.error_message = exc.message

    def action_add_task(self) -> None:
        """Open add task dialog."""
        if self._task_service is None or self.selected_list is None:
            self.error_message = "Select a list first"
            return

        def on_result(result: dict[str, object] | None) -> None:
            if result is None:
                return
            try:
                from datetime import datetime
                from mtd.domain.models import TaskImportance

                title = str(result.get("title", ""))
                importance_str = str(result.get("importance", "normal"))
                importance = TaskImportance(importance_str)
                due_at = None
                due_data = result.get("dueDateTime")
                if due_data and isinstance(due_data, dict):
                    due_str = due_data.get("dateTime", "")
                    if due_str:
                        due_at = datetime.fromisoformat(due_str)

                self._task_service.create_task(
                    self.selected_list.display_name,
                    title,
                    due_at=due_at,
                    importance=importance,
                )
                self.refresh_tasks()
                self.error_message = "Task created"
            except MtdError as exc:
                self.error_message = exc.message
            except Exception as exc:
                self.error_message = f"Failed to create task: {exc}"

        self.push_screen(
            AddTaskScreen(self.selected_list.display_name),
            callback=on_result,
        )

    def action_delete_task(self) -> None:
        """Delete selected task with confirmation."""
        if self._task_service is None or self.selected_task is None or self.selected_list is None:
            return
        task = self.selected_task
        try:
            self._task_service.delete_task(
                self.selected_list.display_name, task.id
            )
            self.selected_task = None
            self.refresh_tasks()
            self.error_message = "Task deleted"
        except MtdError as exc:
            self.error_message = exc.message

    def action_edit_task(self) -> None:
        """Open edit task dialog."""
        if self._task_service is None or self.selected_task is None or self.selected_list is None:
            self.error_message = "Select a task first"
            return

        task = self.selected_task

        def on_result(result: dict[str, object] | None) -> None:
            if result is None or not result:
                return
            try:
                from datetime import datetime
                from mtd.domain.models import TaskImportance

                kwargs: dict[str, object] = {}
                if "title" in result:
                    kwargs["title"] = str(result["title"])
                if "importance" in result:
                    kwargs["importance"] = TaskImportance(str(result["importance"]))
                due_data = result.get("dueDateTime")
                if due_data and isinstance(due_data, dict):
                    due_str = due_data.get("dateTime", "")
                    if due_str:
                        kwargs["due_at"] = datetime.fromisoformat(due_str)

                self._task_service.update_task(
                    self.selected_list.display_name, task.id, **kwargs
                )
                self.refresh_tasks()
                self.error_message = "Task updated"
            except MtdError as exc:
                self.error_message = exc.message
            except Exception as exc:
                self.error_message = f"Failed to update task: {exc}"

        self.push_screen(EditTaskScreen(task), callback=on_result)

    def action_search(self) -> None:
        """Activate task search."""
        # Simple search: filter tasks by title containing query
        # In a real implementation, this would show an input bar
        # For now, cycle through preset queries as a demo
        queries = ["", "review", "call", "meeting"]
        try:
            idx = queries.index(self.search_query)
            self.search_query = queries[(idx + 1) % len(queries)]
        except ValueError:
            self.search_query = queries[0]
        self._apply_task_display()

    def _apply_task_display(self) -> None:
        """Apply search, filter, and sort to tasks."""
        if not self.tasks:
            return
        result = list(self.tasks)

        # Filter by status
        if self.task_filter == "active":
            result = [t for t in result if t.status.value != "completed"]
        elif self.task_filter == "completed":
            result = [t for t in result if t.status.value == "completed"]

        # Search by title
        if self.search_query:
            query = self.search_query.lower()
            result = [t for t in result if query in t.title.lower()]

        # Sort
        if self.sort_mode == "due":
            result.sort(key=lambda t: t.due_at or datetime.max.replace(tzinfo=UTC))
        elif self.sort_mode == "importance":
            importance_order = {"high": 0, "normal": 1, "low": 2}
            result.sort(key=lambda t: importance_order.get(t.importance.value, 1))
        elif self.sort_mode == "title":
            result.sort(key=lambda t: t.title.lower())

        # Update display without changing the underlying tasks reactive
        # We do this by dispatching to the task table directly
        self.query_one("#task-pane", TaskTable)._display_filtered(result)

    def action_sort_tasks(self) -> None:
        """Cycle sort mode."""
        modes = ["due", "importance", "title"]
        try:
            idx = modes.index(self.sort_mode)
            self.sort_mode = modes[(idx + 1) % len(modes)]
        except ValueError:
            self.sort_mode = modes[0]
        self.error_message = f"Sort: {self.sort_mode}"
        self._apply_task_display()

    def action_filter_all(self) -> None:
        """Show all tasks."""
        self.task_filter = "all"
        self._apply_task_display()

    def action_filter_active(self) -> None:
        """Show active tasks only."""
        self.task_filter = "active"
        self._apply_task_display()

    def action_filter_completed(self) -> None:
        """Show completed tasks only."""
        self.task_filter = "completed"
        self._apply_task_display()

    def action_help(self) -> None:
        """Show help overlay."""
        self.push_screen(HelpScreen())

    def action_toggle_detail(self) -> None:
        """Toggle detail pane visibility."""
        detail = self.query_one("#detail-pane", TaskDetail)
        sidebar = self.query_one("#sidebar", ListSidebar)
        task_pane = self.query_one("#task-pane", TaskTable)
        if detail.display:
            detail.display = False
            sidebar.styles.width = "30%"
            task_pane.styles.width = "70%"
        else:
            detail.display = True
            sidebar.styles.width = "25%"
            task_pane.styles.width = "45%"
