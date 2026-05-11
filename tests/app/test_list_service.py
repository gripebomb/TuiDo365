"""Tests for the list application service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mtd.app.services.list_service import ListService
from mtd.domain.errors import BuiltInListError, GraphNetworkError, GraphNotFoundError
from mtd.domain.models import TaskList


@pytest.fixture
def mock_api() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_cache() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_api: MagicMock) -> ListService:
    return ListService(mock_api)


class TestGetLists:
    """Verify get_lists delegates to the repository."""

    def test_returns_lists(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = [
            TaskList(id="1", displayName="Tasks"),
            TaskList(id="2", displayName="Work"),
        ]
        result, freshness = service.get_lists()
        assert len(result) == 2
        assert result[0].display_name == "Tasks"
        assert freshness.source == "graph"

    def test_empty(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = []
        result, freshness = service.get_lists()
        assert result == []
        assert freshness.source == "graph"

    def test_saves_to_cache(self, mock_api: MagicMock, mock_cache: MagicMock) -> None:
        service = ListService(mock_api, mock_cache)
        mock_api.list_lists.return_value = [TaskList(id="1", displayName="Tasks")]
        service.get_lists()
        mock_cache.save_lists.assert_called_once()

    def test_fallback_on_network_error(self, mock_api: MagicMock, mock_cache: MagicMock) -> None:
        service = ListService(mock_api, mock_cache)
        mock_api.list_lists.side_effect = GraphNetworkError("down")
        mock_cache.get_lists.return_value = [TaskList(id="1", displayName="Tasks")]
        result, freshness = service.get_lists()
        assert result[0].display_name == "Tasks"
        assert freshness.source == "cache"

    def test_fallback_raises_when_no_cache(
        self, mock_api: MagicMock, mock_cache: MagicMock
    ) -> None:
        service = ListService(mock_api, mock_cache)
        mock_api.list_lists.side_effect = GraphNetworkError("down")
        mock_cache.get_lists.return_value = None
        with pytest.raises(GraphNetworkError, match="down"):
            service.get_lists()

    def test_offline_reads_cache(self, mock_api: MagicMock, mock_cache: MagicMock) -> None:
        service = ListService(mock_api, mock_cache)
        mock_cache.get_lists.return_value = [TaskList(id="1", displayName="Tasks")]
        result, freshness = service.get_lists(offline=True)
        assert result[0].display_name == "Tasks"
        assert freshness.source == "cache"
        mock_api.list_lists.assert_not_called()

    def test_offline_raises_when_empty(self, mock_api: MagicMock, mock_cache: MagicMock) -> None:
        service = ListService(mock_api, mock_cache)
        mock_cache.get_lists.return_value = None
        with pytest.raises(GraphNetworkError, match="No cached lists"):
            service.get_lists(offline=True)


class TestCreateList:
    """Verify list creation."""

    def test_creates_list(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.create_list.return_value = TaskList(id="3", displayName="Shopping")
        result = service.create_list("Shopping")
        assert result.display_name == "Shopping"
        mock_api.create_list.assert_called_once_with("Shopping")


class TestRenameList:
    """Verify list rename with built-in guards."""

    def test_renames_custom_list(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = [
            TaskList(id="1", displayName="Work", wellknownListName="none"),
        ]
        mock_api.rename_list.return_value = TaskList(id="1", displayName="Projects")
        result = service.rename_list("Work", "Projects")
        assert result.display_name == "Projects"
        mock_api.rename_list.assert_called_once_with("1", "Projects")

    def test_blocks_builtin_list(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = [
            TaskList(
                id="1",
                displayName="Tasks",
                wellknownListName="defaultList",
            ),
        ]
        with pytest.raises(BuiltInListError, match="Cannot rename"):
            service.rename_list("Tasks", "New Name")

    def test_raises_when_not_found(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = []
        with pytest.raises(GraphNotFoundError, match="'Missing' not found"):
            service.rename_list("Missing", "X")


class TestDeleteList:
    """Verify list deletion with built-in guards."""

    def test_deletes_custom_list(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = [
            TaskList(id="1", displayName="Work", wellknownListName="none"),
        ]
        service.delete_list("Work")
        mock_api.delete_list.assert_called_once_with("1")

    def test_blocks_builtin_list(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = [
            TaskList(
                id="1",
                displayName="Flagged Emails",
                wellknownListName="flaggedEmails",
            ),
        ]
        with pytest.raises(BuiltInListError, match="Cannot delete"):
            service.delete_list("Flagged Emails")

    def test_raises_when_not_found(self, service: ListService, mock_api: MagicMock) -> None:
        mock_api.list_lists.return_value = []
        with pytest.raises(GraphNotFoundError, match="'Missing' not found"):
            service.delete_list("Missing")
