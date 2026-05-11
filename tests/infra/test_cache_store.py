"""Tests for the SQLite cache repository."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from mtd.domain.models import Task, TaskList
from mtd.infra.cache.store import CacheRepository


@pytest.fixture
def cache(tmp_path: Path) -> CacheRepository:
    return CacheRepository(db_path=tmp_path / "cache.db")


class TestSaveAndGetLists:
    """Verify list caching round-trip."""

    def test_empty_cache_returns_none(self, cache: CacheRepository) -> None:
        assert cache.get_lists() is None

    def test_save_and_retrieve(self, cache: CacheRepository) -> None:
        lists = [
            TaskList(id="l1", displayName="Tasks", wellknownListName="defaultList"),
            TaskList(id="l2", displayName="Work"),
        ]
        cache.save_lists(lists)
        result = cache.get_lists()
        assert result is not None
        assert len(result) == 2
        assert result[0].id == "l1"
        assert result[0].display_name == "Tasks"
        assert result[1].id == "l2"

    def test_overwrites_previous(self, cache: CacheRepository) -> None:
        cache.save_lists([TaskList(id="l1", displayName="Old")])
        cache.save_lists([TaskList(id="l2", displayName="New")])
        result = cache.get_lists()
        assert result is not None
        assert len(result) == 1
        assert result[0].id == "l2"

    def test_synced_at(self, cache: CacheRepository) -> None:
        before = datetime.now(UTC)
        cache.save_lists([TaskList(id="l1", displayName="Tasks")])
        after = datetime.now(UTC)
        synced = cache.get_lists_synced_at()
        assert synced is not None
        assert before <= synced <= after


class TestSaveAndGetTasks:
    """Verify task caching round-trip."""

    def test_empty_cache_returns_none(self, cache: CacheRepository) -> None:
        assert cache.get_tasks("l1") is None

    def test_save_and_retrieve(self, cache: CacheRepository) -> None:
        tasks = [
            Task(id="t1", listId="l1", title="A", status="notStarted"),
            Task(id="t2", listId="l1", title="B", status="completed"),
        ]
        cache.save_tasks("l1", tasks)
        result = cache.get_tasks("l1")
        assert result is not None
        assert len(result) == 2
        assert result[0].title == "A"
        assert result[1].title == "B"
        assert result[0].list_id == "l1"

    def test_per_list_isolation(self, cache: CacheRepository) -> None:
        cache.save_tasks("l1", [Task(id="t1", listId="l1", title="L1")])
        cache.save_tasks("l2", [Task(id="t2", listId="l2", title="L2")])
        assert cache.get_tasks("l1")[0].title == "L1"
        assert cache.get_tasks("l2")[0].title == "L2"

    def test_overwrites_per_list(self, cache: CacheRepository) -> None:
        cache.save_tasks("l1", [Task(id="t1", listId="l1", title="Old")])
        cache.save_tasks("l1", [Task(id="t2", listId="l1", title="New")])
        result = cache.get_tasks("l1")
        assert result is not None
        assert len(result) == 1
        assert result[0].title == "New"

    def test_synced_at(self, cache: CacheRepository) -> None:
        before = datetime.now(UTC)
        cache.save_tasks("l1", [Task(id="t1", listId="l1", title="T")])
        after = datetime.now(UTC)
        synced = cache.get_tasks_synced_at("l1")
        assert synced is not None
        assert before <= synced <= after


class TestClear:
    """Verify cache clearing."""

    def test_removes_all(self, cache: CacheRepository) -> None:
        cache.save_lists([TaskList(id="l1", displayName="Tasks")])
        cache.save_tasks("l1", [Task(id="t1", listId="l1", title="T")])
        cache.clear()
        assert cache.get_lists() is None
        assert cache.get_tasks("l1") is None
        assert cache.get_lists_synced_at() is None
