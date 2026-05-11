"""Tests for the Textual TUI app."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from textual.widgets import Footer, Header

from mtd.app.services.list_service import FreshnessInfo
from mtd.domain.models import Task, TaskList
from mtd.tui.app import MtdApp
from mtd.tui.screens.main_screen import MainScreen
from mtd.tui.widgets.list_sidebar import ListSidebar
from mtd.tui.widgets.task_detail import TaskDetail
from mtd.tui.widgets.task_table import TaskTable


class TestMtdAppState:
    """Verify reactive state management."""

    def test_reactive_defaults(self) -> None:
        app = MtdApp()
        assert app.lists == []
        assert app.tasks == []
        assert app.selected_list is None
        assert app.selected_task is None
        assert app.error_message == ""

    def test_selected_list_clears_selected_task(self) -> None:
        app = MtdApp()
        app.selected_task = Task(id="t1", listId="l1", title="T")
        app.selected_list = TaskList(id="l1", displayName="Tasks")
        assert app.selected_task is None


class TestMtdAppCompose:
    """Verify app composition."""

    @pytest.mark.asyncio
    async def test_composes_main_screen(self) -> None:
        app = MtdApp()
        async with app.run_test() as pilot:
            assert isinstance(pilot.app.screen, MainScreen)

    @pytest.mark.asyncio
    async def test_has_header_footer(self) -> None:
        app = MtdApp()
        async with app.run_test() as pilot:
            screen = pilot.app.screen
            assert len(list(screen.query(Header))) == 1
            assert len(list(screen.query(Footer))) == 1

    @pytest.mark.asyncio
    async def test_has_three_panels(self) -> None:
        app = MtdApp()
        async with app.run_test() as pilot:
            screen = pilot.app.screen
            assert len(list(screen.query(ListSidebar))) == 1
            assert len(list(screen.query(TaskTable))) == 1
            assert len(list(screen.query(TaskDetail))) == 1


class TestMtdAppRefresh:
    """Verify refresh action."""

    def test_refresh_loads_lists(self) -> None:
        app = MtdApp()
        mock_service = MagicMock()
        mock_service.get_lists.return_value = (
            [TaskList(id="1", displayName="Tasks")],
            FreshnessInfo(source="graph"),
        )
        app._list_service = mock_service
        app.action_refresh()
        assert len(app.lists) == 1
        assert app.lists[0].display_name == "Tasks"

    def test_refresh_sets_error(self) -> None:
        from mtd.domain.errors import GraphPermissionError

        app = MtdApp()
        mock_service = MagicMock()
        mock_service.get_lists.side_effect = GraphPermissionError("Denied")
        app._list_service = mock_service
        app.action_refresh()
        assert "Denied" in app.error_message


class TestMtdAppTaskRefresh:
    """Verify task refresh."""

    def test_refresh_tasks_loads_tasks(self) -> None:
        app = MtdApp()
        app.selected_list = TaskList(id="l1", displayName="Tasks")
        mock_service = MagicMock()
        mock_service.get_tasks_by_list_name.return_value = (
            app.selected_list,
            [Task(id="t1", listId="l1", title="T")],
            FreshnessInfo(source="graph"),
        )
        app._task_service = mock_service
        app.refresh_tasks()
        assert len(app.tasks) == 1
        assert app.tasks[0].title == "T"

    def test_refresh_tasks_clears_on_error(self) -> None:
        from mtd.domain.errors import GraphNotFoundError

        app = MtdApp()
        app.selected_list = TaskList(id="l1", displayName="Tasks")
        mock_service = MagicMock()
        mock_service.get_tasks_by_list_name.side_effect = GraphNotFoundError("Gone")
        app._task_service = mock_service
        app.tasks = [Task(id="t1", listId="l1", title="T")]
        app.refresh_tasks()
        assert app.tasks == []
        assert "Gone" in app.error_message
