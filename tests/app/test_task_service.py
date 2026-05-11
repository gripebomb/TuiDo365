"""Tests for the task application service."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from mtd.app.services.task_service import TaskService, _format_datetime
from mtd.domain.errors import GraphNetworkError, GraphNotFoundError
from mtd.domain.models import Task, TaskImportance, TaskList


@pytest.fixture
def mock_api() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_cache() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_api: MagicMock) -> TaskService:
    return TaskService(mock_api)


class TestGetTasksByListName:
    """Verify lookup by list display name."""

    def test_returns_list_and_tasks(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        tasks = [Task(id="t1", listId="list-1", title="Task 1")]
        mock_api.list_lists.return_value = [task_list]
        mock_api.list_tasks.return_value = tasks

        result_list, result_tasks, freshness = service.get_tasks_by_list_name("Tasks")

        assert result_list.id == "list-1"
        assert result_tasks == tasks
        assert freshness.source == "graph"

    def test_saves_to_cache(self, mock_api: MagicMock, mock_cache: MagicMock) -> None:
        service = TaskService(mock_api, mock_cache)
        task_list = TaskList(id="list-1", displayName="Tasks")
        tasks = [Task(id="t1", listId="list-1", title="Task 1")]
        mock_api.list_lists.return_value = [task_list]
        mock_api.list_tasks.return_value = tasks

        service.get_tasks_by_list_name("Tasks")
        mock_cache.save_tasks.assert_called_once_with("list-1", tasks)

    def test_raises_when_list_not_found(self, service: TaskService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = [TaskList(id="1", displayName="Work")]
        with pytest.raises(GraphNotFoundError, match="'Personal' not found"):
            service.get_tasks_by_list_name("Personal")

    def test_detail_includes_available_lists(
        self, service: TaskService, mock_api: MagicMock
    ) -> None:
        mock_api.list_lists.return_value = [
            TaskList(id="1", displayName="Work"),
            TaskList(id="2", displayName="Shopping"),
        ]
        with pytest.raises(GraphNotFoundError) as exc_info:
            service.get_tasks_by_list_name("Personal")

        assert "Work" in exc_info.value.detail
        assert "Shopping" in exc_info.value.detail

    def test_detail_when_no_lists(self, service: TaskService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = []
        with pytest.raises(GraphNotFoundError) as exc_info:
            service.get_tasks_by_list_name("Personal")

        assert "No lists found" in exc_info.value.detail

    def test_fallback_on_network_error(self, mock_api: MagicMock, mock_cache: MagicMock) -> None:
        service = TaskService(mock_api, mock_cache)
        task_list = TaskList(id="l1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]
        mock_api.list_tasks.side_effect = GraphNetworkError("down")
        mock_cache.get_lists.return_value = [task_list]
        mock_cache.get_tasks.return_value = [Task(id="t1", listId="l1", title="T")]

        result_list, result_tasks, freshness = service.get_tasks_by_list_name("Tasks")

        assert result_list.display_name == "Tasks"
        assert freshness.source == "cache"

    def test_offline_reads_cache(self, mock_api: MagicMock, mock_cache: MagicMock) -> None:
        service = TaskService(mock_api, mock_cache)
        task_list = TaskList(id="l1", displayName="Tasks")
        mock_cache.get_lists.return_value = [task_list]
        mock_cache.get_tasks.return_value = [Task(id="t1", listId="l1", title="T")]

        result_list, result_tasks, freshness = service.get_tasks_by_list_name("Tasks", offline=True)

        assert result_list.display_name == "Tasks"
        assert result_tasks[0].title == "T"
        assert freshness.source == "cache"
        mock_api.list_lists.assert_not_called()

    def test_offline_raises_when_no_list_cache(
        self, mock_api: MagicMock, mock_cache: MagicMock
    ) -> None:
        service = TaskService(mock_api, mock_cache)
        mock_cache.get_lists.return_value = None
        with pytest.raises(GraphNetworkError, match="No cached lists"):
            service.get_tasks_by_list_name("Tasks", offline=True)


class TestCreateTask:
    """Verify task creation."""

    def test_creates_task(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]
        mock_api.create_task.return_value = Task(id="new", listId="list-1", title="Buy milk")

        result = service.create_task("Tasks", "Buy milk")

        assert result.title == "Buy milk"
        mock_api.create_task.assert_called_once_with(
            "list-1", {"title": "Buy milk", "importance": "normal"}
        )

    def test_with_due_date(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]
        due = datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC)
        mock_api.create_task.return_value = Task(id="new", listId="list-1", title="Buy milk")

        service.create_task("Tasks", "Buy milk", due_at=due)

        payload = mock_api.create_task.call_args[0][1]
        assert payload["dueDateTime"]["dateTime"] == "2026-04-25T12:00:00+00:00"
        assert payload["dueDateTime"]["timeZone"] == "UTC"

    def test_with_importance(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]
        mock_api.create_task.return_value = Task(id="new", listId="list-1", title="Urgent")

        service.create_task("Tasks", "Urgent", importance=TaskImportance.HIGH)

        payload = mock_api.create_task.call_args[0][1]
        assert payload["importance"] == "high"


class TestCompleteTask:
    """Verify task completion."""

    def test_completes_task(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]
        mock_api.update_task.return_value = Task(
            id="t1", listId="list-1", title="Done", status="completed"
        )

        result = service.complete_task("Tasks", "t1")

        assert result.status.value == "completed"
        mock_api.update_task.assert_called_once_with("list-1", "t1", {"status": "completed"})


class TestUpdateTask:
    """Verify task update."""

    def test_updates_title(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]
        mock_api.update_task.return_value = Task(id="t1", listId="list-1", title="New title")

        result = service.update_task("Tasks", "t1", title="New title")

        assert result.title == "New title"
        mock_api.update_task.assert_called_once_with("list-1", "t1", {"title": "New title"})

    def test_updates_multiple_fields(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]
        mock_api.update_task.return_value = Task(id="t1", listId="list-1", title="T")
        due = datetime(2026, 4, 25, tzinfo=UTC)

        service.update_task("Tasks", "t1", title="T", due_at=due, importance=TaskImportance.HIGH)

        payload = mock_api.update_task.call_args[0][2]
        assert payload["title"] == "T"
        assert payload["importance"] == "high"
        assert "dueDateTime" in payload


class TestDeleteTask:
    """Verify task deletion."""

    def test_deletes_task(self, service: TaskService, mock_api: MagicMock) -> None:
        task_list = TaskList(id="list-1", displayName="Tasks")
        mock_api.list_lists.return_value = [task_list]

        service.delete_task("Tasks", "t1")

        mock_api.delete_task.assert_called_once_with("list-1", "t1")


class TestFormatDatetime:
    """Verify datetime formatting for Graph."""

    def test_aware_datetime(self) -> None:
        dt = datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC)
        result = _format_datetime(dt)
        assert result["dateTime"] == "2026-04-25T12:00:00+00:00"
        assert result["timeZone"] == "UTC"

    def test_naive_datetime_gets_utc(self) -> None:
        dt = datetime(2026, 4, 25, 12, 0, 0)
        result = _format_datetime(dt)
        assert "+00:00" in result["dateTime"]
        assert result["timeZone"] == "UTC"
