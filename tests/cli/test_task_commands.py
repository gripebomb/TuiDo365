"""Tests for CLI task commands."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mtd.app.services.list_service import FreshnessInfo
from mtd.cli.app import app
from mtd.domain.errors import GraphNotFoundError
from mtd.domain.models import Task, TaskList

runner = CliRunner()


@pytest.fixture
def mock_task_service() -> MagicMock:
    return MagicMock()


class TestTasks:
    """Verify ``mtd tasks --list <name>`` behavior."""

    def test_success_table(self, mock_task_service: MagicMock) -> None:
        task_list = TaskList(id="1", displayName="Tasks")
        tasks = [
            Task(id="t1", listId="1", title="Buy milk", status="notStarted"),
            Task(id="t2", listId="1", title="Call dentist", status="completed"),
        ]
        mock_task_service.get_tasks_by_list_name.return_value = (
            task_list,
            tasks,
            FreshnessInfo(source="graph"),
        )
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(app, ["tasks", "--list", "Tasks"])

        assert result.exit_code == 0
        assert "Buy milk" in result.output
        assert "Call dentist" in result.output
        mock_task_service.get_tasks_by_list_name.assert_called_once_with("Tasks", offline=False)

    def test_json_output(self, mock_task_service: MagicMock) -> None:
        task_list = TaskList(id="1", displayName="Tasks")
        due = datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC)
        tasks = [Task(id="t1", listId="1", title="Buy milk", dueDateTime=due)]
        mock_task_service.get_tasks_by_list_name.return_value = (
            task_list,
            tasks,
            FreshnessInfo(source="graph"),
        )
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(app, ["tasks", "--list", "Tasks", "--json"])

        assert result.exit_code == 0
        assert '"title": "Buy milk"' in result.output
        assert "Tasks" in result.output

    def test_handles_not_found(self, mock_task_service: MagicMock) -> None:
        exc = GraphNotFoundError("List 'Missing' not found.", detail="Available: Work")
        mock_task_service.get_tasks_by_list_name.side_effect = exc
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(app, ["tasks", "--list", "Missing"])

        assert result.exit_code == 1
        assert "List 'Missing' not found" in result.output
        assert "Available: Work" in result.output

    def test_not_configured(self) -> None:
        with patch("mtd.cli.task_commands.MtdSettings") as mock_settings_cls:
            mock_settings_cls.return_value.is_configured.return_value = False
            result = runner.invoke(app, ["tasks", "--list", "Tasks"])

        assert result.exit_code == 1
        assert "client_id is not configured" in result.output


class TestAdd:
    """Verify ``mtd add`` behavior."""

    def test_success(self, mock_task_service: MagicMock) -> None:
        mock_task_service.create_task.return_value = Task(id="new", listId="1", title="Buy milk")
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(app, ["add", "--list", "Tasks", "--title", "Buy milk"])

        assert result.exit_code == 0
        assert "Created task: Buy milk" in result.output
        mock_task_service.create_task.assert_called_once()

    def test_with_due_date(self, mock_task_service: MagicMock) -> None:
        mock_task_service.create_task.return_value = Task(id="new", listId="1", title="Buy milk")
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(
                app, ["add", "--list", "Tasks", "--title", "Buy milk", "--due", "2026-04-25"]
            )

        assert result.exit_code == 0
        args, kwargs = mock_task_service.create_task.call_args
        assert kwargs["due_at"] is not None

    def test_json_output(self, mock_task_service: MagicMock) -> None:
        mock_task_service.create_task.return_value = Task(id="new", listId="1", title="Buy milk")
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(app, ["add", "--list", "Tasks", "--title", "Buy milk", "--json"])

        assert result.exit_code == 0
        assert '"title": "Buy milk"' in result.output


class TestDone:
    """Verify ``mtd done`` behavior."""

    def test_success(self, mock_task_service: MagicMock) -> None:
        mock_task_service.complete_task.return_value = Task(
            id="t1", listId="1", title="Buy milk", status="completed"
        )
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(app, ["done", "--list", "Tasks", "--task-id", "t1"])

        assert result.exit_code == 0
        assert "Completed: Buy milk" in result.output
        mock_task_service.complete_task.assert_called_once_with("Tasks", "t1")


class TestUpdate:
    """Verify ``mtd update`` behavior."""

    def test_success(self, mock_task_service: MagicMock) -> None:
        mock_task_service.update_task.return_value = Task(id="t1", listId="1", title="New title")
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(
                app,
                [
                    "update",
                    "--list",
                    "Tasks",
                    "--task-id",
                    "t1",
                    "--title",
                    "New title",
                ],
            )

        assert result.exit_code == 0
        assert "Updated task: New title" in result.output
        mock_task_service.update_task.assert_called_once_with(
            "Tasks", "t1", title="New title", due_at=None, importance=None
        )


class TestDelete:
    """Verify ``mtd delete`` behavior."""

    def test_success(self, mock_task_service: MagicMock) -> None:
        with patch("mtd.cli.task_commands._task_service", return_value=mock_task_service):
            result = runner.invoke(app, ["delete", "--list", "Tasks", "--task-id", "t1"])

        assert result.exit_code == 0
        assert "Task deleted" in result.output
        mock_task_service.delete_task.assert_called_once_with("Tasks", "t1")
