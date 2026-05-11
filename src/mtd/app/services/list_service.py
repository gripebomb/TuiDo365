"""Application service for task list operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from mtd.domain.errors import BuiltInListError, GraphNetworkError, GraphNotFoundError
from mtd.domain.models import TaskList
from mtd.infra.cache.store import CacheRepository
from mtd.infra.graph.todo_api import TodoApiRepository


@dataclass
class FreshnessInfo:
    """Metadata about how fresh cached data is."""

    source: str  # "graph" or "cache"
    synced_at: datetime | None = None

    def age_seconds(self) -> float | None:
        """Return age in seconds, or ``None`` when unknown."""
        if self.synced_at is None:
            return None
        return (datetime.now(UTC) - self.synced_at).total_seconds()


class ListService:
    """Orchestrates read and write operations on task lists."""

    def __init__(self, api: TodoApiRepository, cache: CacheRepository | None = None) -> None:
        self._api = api
        self._cache = cache

    # ── reads ──────────────────────────────────────────────────────────

    def get_lists(self, *, offline: bool = False) -> tuple[list[TaskList], FreshnessInfo]:
        """Return all task lists for the authenticated user.

        Args:
            offline: When ``True``, read from cache without contacting Graph.

        Returns:
            Tuple of task lists and freshness metadata.
        """
        if offline:
            cached = self._cache.get_lists() if self._cache else None
            if cached is None or self._cache is None:
                raise GraphNetworkError("No cached lists available.")
            return cached, FreshnessInfo(
                source="cache",
                synced_at=self._cache.get_lists_synced_at(),
            )

        try:
            lists = self._api.list_lists()
        except GraphNetworkError:
            cached = self._cache.get_lists() if self._cache else None
            if cached is not None and self._cache is not None:
                return cached, FreshnessInfo(
                    source="cache",
                    synced_at=self._cache.get_lists_synced_at(),
                )
            raise

        if self._cache is not None:
            self._cache.save_lists(lists)
        return lists, FreshnessInfo(source="graph")

    # ── writes ─────────────────────────────────────────────────────────

    def create_list(self, display_name: str) -> TaskList:
        """Create a new task list."""
        return self._api.create_list(display_name)

    def rename_list(self, current_name: str, new_name: str) -> TaskList:
        """Rename an existing task list.

        Raises:
            BuiltInListError: When the target list is built-in.
        """
        task_list = self._resolve_list(current_name)
        if task_list.is_builtin:
            raise BuiltInListError(task_list.display_name, "rename")
        return self._api.rename_list(task_list.id, new_name)

    def delete_list(self, display_name: str) -> None:
        """Delete a task list.

        Raises:
            BuiltInListError: When the target list is built-in.
        """
        task_list = self._resolve_list(display_name)
        if task_list.is_builtin:
            raise BuiltInListError(task_list.display_name, "delete")
        self._api.delete_list(task_list.id)

    # ── helpers ────────────────────────────────────────────────────────

    def _resolve_list(self, list_name: str) -> TaskList:
        lists, _ = self.get_lists()
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
