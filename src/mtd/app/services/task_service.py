"""Application service for task operations."""

from __future__ import annotations

from datetime import UTC, datetime

from mtd.domain.errors import GraphNetworkError, GraphNotFoundError
from mtd.domain.models import Task, TaskImportance, TaskList
from mtd.infra.cache.store import CacheRepository
from mtd.infra.graph.todo_api import TodoApiRepository

from .list_service import FreshnessInfo


class TaskService:
    """Orchestrates read and write operations on tasks."""

    def __init__(self, api: TodoApiRepository, cache: CacheRepository | None = None) -> None:
        self._api = api
        self._cache = cache

    # ── reads ──────────────────────────────────────────────────────────

    def get_tasks_by_list_name(
        self, list_name: str, *, offline: bool = False
    ) -> tuple[TaskList, list[Task], FreshnessInfo]:
        """Return a task list and its tasks, looked up by display name.

        Args:
            list_name: The display name of the task list.
            offline: When ``True``, read from cache without contacting Graph.

        Returns:
            Tuple of the matched :class:`TaskList`, its tasks, and freshness metadata.
        """
        if offline:
            return self._get_tasks_offline(list_name)

        try:
            task_list = self._resolve_list(list_name)
            tasks = self._api.list_tasks(task_list.id)
        except GraphNetworkError:
            return self._get_tasks_offline(list_name)

        if self._cache is not None:
            self._cache.save_tasks(task_list.id, tasks)
        return task_list, tasks, FreshnessInfo(source="graph")

    def _get_tasks_offline(self, list_name: str) -> tuple[TaskList, list[Task], FreshnessInfo]:
        if self._cache is None:
            raise GraphNetworkError("No cache configured.")
        lists = self._cache.get_lists()
        if lists is None:
            raise GraphNetworkError("No cached lists available.")
        task_list = next(
            (lst for lst in lists if lst.display_name == list_name),
            None,
        )
        if task_list is None:
            raise GraphNotFoundError(
                f"List '{list_name}' not found in cache.",
            )
        tasks = self._cache.get_tasks(task_list.id)
        if tasks is None:
            raise GraphNetworkError(
                f"No cached tasks for list '{list_name}'.",
            )
        return (
            task_list,
            tasks,
            FreshnessInfo(
                source="cache",
                synced_at=self._cache.get_tasks_synced_at(task_list.id),
            ),
        )

    # ── writes ─────────────────────────────────────────────────────────

    def create_task(
        self,
        list_name: str,
        title: str,
        *,
        due_at: datetime | None = None,
        importance: TaskImportance = TaskImportance.NORMAL,
    ) -> Task:
        """Create a new task in the named list."""
        task_list = self._resolve_list(list_name)
        payload: dict[str, object] = {
            "title": title,
            "importance": importance.value,
        }
        if due_at is not None:
            payload["dueDateTime"] = _format_datetime(due_at)
        return self._api.create_task(task_list.id, payload)

    def complete_task(self, list_name: str, task_id: str) -> Task:
        """Mark a task as completed."""
        task_list = self._resolve_list(list_name)
        return self._api.update_task(task_list.id, task_id, {"status": "completed"})

    def update_task(
        self,
        list_name: str,
        task_id: str,
        *,
        title: str | None = None,
        due_at: datetime | None = None,
        importance: TaskImportance | None = None,
    ) -> Task:
        """Update an existing task."""
        task_list = self._resolve_list(list_name)
        payload: dict[str, object] = {}
        if title is not None:
            payload["title"] = title
        if due_at is not None:
            payload["dueDateTime"] = _format_datetime(due_at)
        if importance is not None:
            payload["importance"] = importance.value
        return self._api.update_task(task_list.id, task_id, payload)

    def delete_task(self, list_name: str, task_id: str) -> None:
        """Delete a task."""
        task_list = self._resolve_list(list_name)
        self._api.delete_task(task_list.id, task_id)

    def get_all_tasks(self) -> list[Task]:
        """Fetch all tasks from all lists."""
        lists = self._api.list_lists()
        if self._cache is not None:
            self._cache.save_lists(lists)
        all_tasks: list[Task] = []
        for task_list in lists:
            try:
                tasks = self._api.list_tasks(task_list.id)
                if self._cache is not None:
                    self._cache.save_tasks(task_list.id, tasks)
                all_tasks.extend(tasks)
            except GraphNetworkError:
                continue
        return all_tasks

    def get_important_tasks(self) -> list[Task]:
        """Get all high-importance tasks across all lists."""
        return [t for t in self.get_all_tasks() if t.importance.value == "high"]

    def get_planned_tasks(self) -> list[Task]:
        """Get all tasks with due dates across all lists."""
        return [t for t in self.get_all_tasks() if t.due_at is not None]

    # ── helpers ────────────────────────────────────────────────────────

    def _resolve_list(self, list_name: str) -> TaskList:
        if self._cache is not None:
            lists = self._cache.get_lists()
            if lists is not None:
                task_list = next(
                    (lst for lst in lists if lst.display_name == list_name),
                    None,
                )
                if task_list is not None:
                    return task_list
        lists = self._api.list_lists()
        if self._cache is not None:
            self._cache.save_lists(lists)
        task_list = next(
            (lst for lst in lists if lst.display_name == list_name),
            None,
        )
        if task_list is None:
            available = [lst.display_name for lst in lists]
            raise GraphNotFoundError(
                f"List '{list_name}' not found.",
                detail=f"Available lists: {available}" if available else "No lists found.",
            )
        return task_list


def _format_datetime(dt: datetime) -> dict[str, str]:
    """Format a datetime for Graph's dateTimeTimeZone shape."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return {"dateTime": dt.isoformat(), "timeZone": "UTC"}
