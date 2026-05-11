"""Microsoft Graph To Do API repository.

Maps Graph response payloads into project-owned domain models at the
infrastructure boundary.
"""

from __future__ import annotations

from typing import Any

from mtd.domain.models import Task, TaskList
from mtd.infra.graph.client import GraphClient


def _map_task(raw: dict[str, Any], list_id: str) -> Task:
    """Transform a Graph task dict into a :class:`Task` model.

    Handles OData annotations (e.g. ``@odata.etag``) and injects the
    parent ``list_id`` because Graph does not include it in task objects.
    """
    data = dict(raw)
    data["listId"] = list_id
    etag = data.pop("@odata.etag", None)
    if etag is not None:
        data["etag"] = etag
    return Task(**data)


class TodoApiRepository:
    """Repository for Microsoft To Do Graph endpoints."""

    def __init__(self, client: GraphClient) -> None:
        self._client = client

    def list_lists(self) -> list[TaskList]:
        """Fetch all task lists for the authenticated user.

        Returns:
            List of :class:`TaskList` domain models.
        """
        response = self._client.get("/me/todo/lists")
        values: list[dict[str, Any]] = response.get("value", [])
        return [TaskList(**item) for item in values]

    def list_tasks(self, list_id: str) -> list[Task]:
        """Fetch all tasks in the given task list.

        Args:
            list_id: The Graph ID of the task list.

        Returns:
            List of :class:`Task` domain models.
        """
        response = self._client.get(f"/me/todo/lists/{list_id}/tasks")
        values: list[dict[str, Any]] = response.get("value", [])
        return [_map_task(item, list_id) for item in values]

    def create_task(self, list_id: str, payload: dict[str, Any]) -> Task:
        """Create a new task in the given list.

        Args:
            list_id: The Graph ID of the task list.
            payload: Graph task payload (e.g. ``{"title": "...", "dueDateTime": "..."}``).

        Returns:
            The created :class:`Task`.
        """
        response = self._client.request("POST", f"/me/todo/lists/{list_id}/tasks", json=payload)
        return _map_task(response, list_id)

    def update_task(self, list_id: str, task_id: str, payload: dict[str, Any]) -> Task:
        """Update an existing task.

        Args:
            list_id: The Graph ID of the task list.
            task_id: The Graph ID of the task.
            payload: Fields to update.

        Returns:
            The updated :class:`Task`.
        """
        response = self._client.request(
            "PATCH", f"/me/todo/lists/{list_id}/tasks/{task_id}", json=payload
        )
        return _map_task(response, list_id)

    def delete_task(self, list_id: str, task_id: str) -> None:
        """Delete a task.

        Args:
            list_id: The Graph ID of the task list.
            task_id: The Graph ID of the task.
        """
        self._client.request("DELETE", f"/me/todo/lists/{list_id}/tasks/{task_id}")

    def create_list(self, display_name: str) -> TaskList:
        """Create a new task list.

        Args:
            display_name: Name for the new list.

        Returns:
            The created :class:`TaskList`.
        """
        response = self._client.request(
            "POST", "/me/todo/lists", json={"displayName": display_name}
        )
        return TaskList(**response)

    def rename_list(self, list_id: str, display_name: str) -> TaskList:
        """Rename an existing task list.

        Args:
            list_id: The Graph ID of the task list.
            display_name: New display name.

        Returns:
            The updated :class:`TaskList`.
        """
        response = self._client.request(
            "PATCH", f"/me/todo/lists/{list_id}", json={"displayName": display_name}
        )
        return TaskList(**response)

    def delete_list(self, list_id: str) -> None:
        """Delete a task list.

        Args:
            list_id: The Graph ID of the task list.
        """
        self._client.request("DELETE", f"/me/todo/lists/{list_id}")
