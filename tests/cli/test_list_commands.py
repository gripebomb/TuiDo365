"""Tests for CLI list commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mtd.app.services.list_service import FreshnessInfo
from mtd.cli.app import app
from mtd.domain.errors import BuiltInListError, GraphNotFoundError, GraphPermissionError
from mtd.domain.models import TaskList

runner = CliRunner()


@pytest.fixture
def mock_list_service() -> MagicMock:
    return MagicMock()


class TestLists:
    """Verify ``mtd lists`` behavior."""

    def test_success_table(self, mock_list_service: MagicMock) -> None:
        mock_list_service.get_lists.return_value = (
            [
                TaskList(id="1", displayName="Tasks", wellknownListName="defaultList"),
                TaskList(id="2", displayName="Work", isShared=True),
            ],
            FreshnessInfo(source="graph"),
        )
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["lists"])

        assert result.exit_code == 0
        assert "Tasks" in result.output
        assert "Work" in result.output

    def test_json_output(self, mock_list_service: MagicMock) -> None:
        mock_list_service.get_lists.return_value = (
            [TaskList(id="1", displayName="Tasks")],
            FreshnessInfo(source="graph"),
        )
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["lists", "--json"])

        assert result.exit_code == 0
        assert '"display_name": "Tasks"' in result.output

    def test_handles_error(self, mock_list_service: MagicMock) -> None:
        mock_list_service.get_lists.side_effect = GraphPermissionError("Access denied")
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["lists"])

        assert result.exit_code == 1
        assert "Access denied" in result.output

    def test_not_configured(self) -> None:
        with patch("mtd.cli.list_commands.MtdSettings") as mock_settings_cls:
            mock_settings_cls.return_value.is_configured.return_value = False
            result = runner.invoke(app, ["lists"])

        assert result.exit_code == 1
        assert "client_id is not configured" in result.output


class TestListCreate:
    """Verify ``mtd list-create`` behavior."""

    def test_success(self, mock_list_service: MagicMock) -> None:
        mock_list_service.create_list.return_value = TaskList(id="3", displayName="Shopping")
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["list-create", "--name", "Shopping"])

        assert result.exit_code == 0
        assert "Created list: Shopping" in result.output

    def test_json_output(self, mock_list_service: MagicMock) -> None:
        mock_list_service.create_list.return_value = TaskList(id="3", displayName="Shopping")
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["list-create", "--name", "Shopping", "--json"])

        assert result.exit_code == 0
        assert '"display_name": "Shopping"' in result.output


class TestListRename:
    """Verify ``mtd list-rename`` behavior."""

    def test_success(self, mock_list_service: MagicMock) -> None:
        mock_list_service.rename_list.return_value = TaskList(id="1", displayName="Projects")
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["list-rename", "--name", "Work", "--new-name", "Projects"])

        assert result.exit_code == 0
        assert "Renamed" in result.output
        assert "Projects" in result.output

    def test_blocks_builtin(self, mock_list_service: MagicMock) -> None:
        mock_list_service.rename_list.side_effect = BuiltInListError("Tasks", "rename")
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["list-rename", "--name", "Tasks", "--new-name", "X"])

        assert result.exit_code == 1
        assert "Cannot rename" in result.output


class TestListDelete:
    """Verify ``mtd list-delete`` behavior."""

    def test_success(self, mock_list_service: MagicMock) -> None:
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["list-delete", "--name", "Old"])

        assert result.exit_code == 0
        assert "Deleted list: 'Old'" in result.output

    def test_blocks_builtin(self, mock_list_service: MagicMock) -> None:
        mock_list_service.delete_list.side_effect = BuiltInListError("Flagged Emails", "delete")
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["list-delete", "--name", "Flagged Emails"])

        assert result.exit_code == 1
        assert "Cannot delete" in result.output

    def test_not_found(self, mock_list_service: MagicMock) -> None:
        mock_list_service.delete_list.side_effect = GraphNotFoundError("List 'X' not found.")
        with patch("mtd.cli.list_commands._list_service", return_value=mock_list_service):
            result = runner.invoke(app, ["list-delete", "--name", "X"])

        assert result.exit_code == 1
        assert "not found" in result.output
