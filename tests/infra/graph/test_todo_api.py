"""Tests for the Graph To Do API repository."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from mtd.domain.models import Task, TaskImportance, TaskList, TaskStatus, WellKnownListName
from mtd.infra.graph.todo_api import TodoApiRepository


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo(mock_client: MagicMock) -> TodoApiRepository:
    return TodoApiRepository(mock_client)


class TestListLists:
    """Verify listing task lists."""

    def test_returns_task_lists(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "value": [
                {
                    "id": "list-1",
                    "displayName": "Tasks",
                    "wellknownListName": "defaultList",
                    "isOwner": True,
                    "isShared": False,
                },
                {
                    "id": "list-2",
                    "displayName": "Work",
                    "wellknownListName": "none",
                    "isOwner": True,
                    "isShared": True,
                },
            ]
        }
        result = repo.list_lists()

        assert len(result) == 2
        assert isinstance(result[0], TaskList)
        assert result[0].id == "list-1"
        assert result[0].display_name == "Tasks"
        assert result[0].wellknown_list_name == WellKnownListName.DEFAULT_LIST
        assert result[1].display_name == "Work"
        assert result[1].is_shared is True

    def test_empty_response(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"value": []}
        result = repo.list_lists()
        assert result == []

    def test_uses_correct_endpoint(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"value": []}
        repo.list_lists()
        mock_client.get.assert_called_once_with("/me/todo/lists")


class TestListTasks:
    """Verify listing tasks."""

    def test_returns_tasks(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "value": [
                {
                    "id": "task-1",
                    "title": "Buy milk",
                    "status": "notStarted",
                    "importance": "normal",
                    "dueDateTime": {"dateTime": "2026-04-25T12:00:00", "timeZone": "UTC"},
                    "@odata.etag": 'W/"abc"',
                },
                {
                    "id": "task-2",
                    "title": "Call dentist",
                    "status": "completed",
                    "importance": "high",
                },
            ]
        }
        result = repo.list_tasks("list-1")

        assert len(result) == 2
        assert isinstance(result[0], Task)
        assert result[0].id == "task-1"
        assert result[0].list_id == "list-1"
        assert result[0].title == "Buy milk"
        assert result[0].status == TaskStatus.NOT_STARTED
        assert result[0].importance == TaskImportance.NORMAL
        assert result[0].due_at == datetime(2026, 4, 25, 12, 0, 0)
        assert result[0].etag == 'W/"abc"'

        assert result[1].id == "task-2"
        assert result[1].status == TaskStatus.COMPLETED
        assert result[1].importance == TaskImportance.HIGH
        assert result[1].etag is None

    def test_handles_graph_datetime_format(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        """Graph returns datetimes as {"dateTime": "...", "timeZone": "..."}."""
        mock_client.get.return_value = {
            "value": [
                {
                    "id": "task-1",
                    "title": "Test task",
                    "status": "notStarted",
                    "completedDateTime": {
                        "dateTime": "2025-12-11T10:30:00",
                        "timeZone": "UTC",
                    },
                    "lastModifiedDateTime": {
                        "dateTime": "2026-01-15T14:22:00",
                        "timeZone": "America/New_York",
                    },
                    "reminderDateTime": {
                        "dateTime": "2025-12-10T09:00:00",
                        "timeZone": "UTC",
                    },
                }
            ]
        }
        result = repo.list_tasks("list-1")
        assert len(result) == 1
        assert result[0].completed_at == datetime(2025, 12, 11, 10, 30, 0)
        assert result[0].last_modified_at is not None
        assert result[0].reminder_at is not None

    def test_empty_response(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"value": []}
        result = repo.list_tasks("list-1")
        assert result == []

    def test_uses_correct_endpoint(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"value": []}
        repo.list_tasks("list-1")
        mock_client.get.assert_called_once_with("/me/todo/lists/list-1/tasks")

    def test_injects_list_id(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "value": [{"id": "task-1", "title": "T", "status": "notStarted"}]
        }
        result = repo.list_tasks("my-list-id")
        assert result[0].list_id == "my-list-id"


class TestCreateTask:
    """Verify task creation."""

    def test_creates_task(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.request.return_value = {
            "id": "new-task",
            "title": "New Task",
            "status": "notStarted",
        }
        result = repo.create_task("list-1", {"title": "New Task"})

        assert result.id == "new-task"
        assert result.title == "New Task"
        assert result.list_id == "list-1"
        mock_client.request.assert_called_once_with(
            "POST", "/me/todo/lists/list-1/tasks", json={"title": "New Task"}
        )


class TestUpdateTask:
    """Verify task update."""

    def test_updates_task(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.request.return_value = {
            "id": "task-1",
            "title": "Updated",
            "status": "inProgress",
        }
        result = repo.update_task("list-1", "task-1", {"title": "Updated"})

        assert result.title == "Updated"
        mock_client.request.assert_called_once_with(
            "PATCH", "/me/todo/lists/list-1/tasks/task-1", json={"title": "Updated"}
        )


class TestDeleteTask:
    """Verify task deletion."""

    def test_deletes_task(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.request.return_value = {}
        repo.delete_task("list-1", "task-1")
        mock_client.request.assert_called_once_with("DELETE", "/me/todo/lists/list-1/tasks/task-1")


class TestCreateList:
    """Verify list creation."""

    def test_creates_list(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.request.return_value = {
            "id": "new-list",
            "displayName": "Shopping",
            "wellknownListName": "none",
        }
        result = repo.create_list("Shopping")

        assert result.id == "new-list"
        assert result.display_name == "Shopping"
        mock_client.request.assert_called_once_with(
            "POST", "/me/todo/lists", json={"displayName": "Shopping"}
        )


class TestRenameList:
    """Verify list rename."""

    def test_renames_list(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.request.return_value = {
            "id": "list-1",
            "displayName": "Groceries",
        }
        result = repo.rename_list("list-1", "Groceries")

        assert result.display_name == "Groceries"
        mock_client.request.assert_called_once_with(
            "PATCH", "/me/todo/lists/list-1", json={"displayName": "Groceries"}
        )


class TestDeleteList:
    """Verify list deletion."""

    def test_deletes_list(self, repo: TodoApiRepository, mock_client: MagicMock) -> None:
        mock_client.request.return_value = {}
        repo.delete_list("list-1")
        mock_client.request.assert_called_once_with("DELETE", "/me/todo/lists/list-1")
