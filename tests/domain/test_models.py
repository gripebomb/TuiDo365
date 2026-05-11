"""Tests for domain models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mtd.domain.models import (
    Task,
    TaskBody,
    TaskImportance,
    TaskList,
    TaskStatus,
    WellKnownListName,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_values(self) -> None:
        assert TaskStatus.NOT_STARTED == "notStarted"
        assert TaskStatus.IN_PROGRESS == "inProgress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.WAITING_ON_OTHERS == "waitingOnOthers"
        assert TaskStatus.DEFERRED == "deferred"

    def test_from_string(self) -> None:
        assert TaskStatus("notStarted") is TaskStatus.NOT_STARTED
        assert TaskStatus("completed") is TaskStatus.COMPLETED

    def test_invalid_string(self) -> None:
        with pytest.raises(ValueError):
            TaskStatus("unknown")

    def test_is_str_subclass(self) -> None:
        assert isinstance(TaskStatus.COMPLETED, str)


class TestTaskImportance:
    """Tests for TaskImportance enum."""

    def test_values(self) -> None:
        assert TaskImportance.LOW == "low"
        assert TaskImportance.NORMAL == "normal"
        assert TaskImportance.HIGH == "high"

    def test_from_string(self) -> None:
        assert TaskImportance("high") is TaskImportance.HIGH

    def test_invalid_string(self) -> None:
        with pytest.raises(ValueError):
            TaskImportance("critical")


class TestWellKnownListName:
    """Tests for WellKnownListName enum."""

    def test_values(self) -> None:
        assert WellKnownListName.NONE == "none"
        assert WellKnownListName.DEFAULT_LIST == "defaultList"
        assert WellKnownListName.FLAGGED_EMAILS == "flaggedEmails"
        assert WellKnownListName.UNKNOWN_FUTURE_VALUE == "unknownFutureValue"


# ---------------------------------------------------------------------------
# TaskList
# ---------------------------------------------------------------------------


class TestTaskList:
    """Tests for the TaskList model."""

    def test_minimal_construction_with_alias(self) -> None:
        task_list = TaskList(id="abc-123", displayName="My Tasks")
        assert task_list.id == "abc-123"
        assert task_list.display_name == "My Tasks"

    def test_construction_with_field_name(self) -> None:
        task_list = TaskList(id="abc-123", display_name="My Tasks")
        assert task_list.display_name == "My Tasks"

    def test_default_values(self) -> None:
        task_list = TaskList(id="abc-123", displayName="Tasks")
        assert task_list.wellknown_list_name == WellKnownListName.NONE
        assert task_list.is_owner is True
        assert task_list.is_shared is False

    def test_all_fields(self) -> None:
        task_list = TaskList(
            id="abc-123",
            displayName="Shared List",
            wellknownListName="defaultList",
            isOwner=False,
            isShared=True,
        )
        assert task_list.wellknown_list_name == WellKnownListName.DEFAULT_LIST
        assert task_list.is_owner is False
        assert task_list.is_shared is True

    def test_populate_by_name_enabled(self) -> None:
        """Both camelCase aliases and snake_case field names should work."""
        from_alias = TaskList(id="x", displayName="From Alias")
        from_name = TaskList(id="x", display_name="From Name")
        assert from_alias.display_name == "From Alias"
        assert from_name.display_name == "From Name"

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            TaskList(displayName="No ID")  # type: ignore[call-arg]

    def test_model_dump(self) -> None:
        task_list = TaskList(id="abc-123", displayName="Tasks")
        data = task_list.model_dump()
        assert data["id"] == "abc-123"
        assert data["display_name"] == "Tasks"

    def test_model_dump_by_alias(self) -> None:
        task_list = TaskList(id="abc-123", displayName="Tasks")
        data = task_list.model_dump(by_alias=True)
        assert "displayName" in data
        assert data["displayName"] == "Tasks"

    def test_is_builtin_false_for_none(self) -> None:
        task_list = TaskList(id="abc-123", displayName="Custom List")
        assert task_list.is_builtin is False

    def test_is_builtin_false_for_unknown_future(self) -> None:
        task_list = TaskList(
            id="abc-123", displayName="Future", wellknownListName="unknownFutureValue"
        )
        assert task_list.is_builtin is False

    def test_is_builtin_true_for_default_list(self) -> None:
        task_list = TaskList(id="abc-123", displayName="Tasks", wellknownListName="defaultList")
        assert task_list.is_builtin is True

    def test_is_builtin_true_for_flagged_emails(self) -> None:
        task_list = TaskList(
            id="abc-123", displayName="Flagged Emails", wellknownListName="flaggedEmails"
        )
        assert task_list.is_builtin is True


# ---------------------------------------------------------------------------
# TaskBody
# ---------------------------------------------------------------------------


class TestTaskBody:
    """Tests for the TaskBody model."""

    def test_default_values(self) -> None:
        body = TaskBody()
        assert body.content == ""
        assert body.content_type == "text"

    def test_with_content(self) -> None:
        body = TaskBody(content="Hello world", contentType="html")
        assert body.content == "Hello world"
        assert body.content_type == "html"

    def test_snake_case_field(self) -> None:
        body = TaskBody(content="Test", content_type="html")
        assert body.content_type == "html"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestTask:
    """Tests for the Task model."""

    def _make_task(self, **overrides: object) -> Task:
        defaults: dict[str, object] = {
            "id": "task-1",
            "listId": "list-1",
            "title": "Test task",
        }
        defaults.update(overrides)
        return Task(**defaults)

    def test_minimal_construction(self) -> None:
        task = self._make_task()
        assert task.id == "task-1"
        assert task.list_id == "list-1"
        assert task.title == "Test task"
        assert task.status == TaskStatus.NOT_STARTED
        assert task.importance == TaskImportance.NORMAL
        assert task.body is None
        assert task.due_at is None
        assert task.start_at is None
        assert task.reminder_at is None
        assert task.completed_at is None
        assert task.last_modified_at is None
        assert task.etag is None
        assert task.categories == []

    def test_construction_with_aliases(self) -> None:
        now = datetime.now(UTC)
        task = self._make_task(
            dueDateTime=now,
            completedDateTime=now,
            lastModifiedDateTime=now,
        )
        assert task.due_at == now
        assert task.completed_at == now
        assert task.last_modified_at == now

    def test_construction_with_field_names(self) -> None:
        now = datetime.now(UTC)
        task = self._make_task(
            due_at=now,
            completed_at=now,
        )
        assert task.due_at == now
        assert task.completed_at == now

    def test_is_completed_false(self) -> None:
        task = self._make_task(status="notStarted")
        assert task.is_completed is False

    def test_is_completed_true(self) -> None:
        task = self._make_task(status="completed")
        assert task.is_completed is True

    def test_is_completed_in_progress(self) -> None:
        task = self._make_task(status="inProgress")
        assert task.is_completed is False

    def test_body_nested_model(self) -> None:
        task = self._make_task(body={"content": "Some notes", "contentType": "html"})
        assert task.body is not None
        assert task.body.content == "Some notes"
        assert task.body.content_type == "html"

    def test_body_none(self) -> None:
        task = self._make_task()
        assert task.body is None

    def test_categories_default_empty(self) -> None:
        task = self._make_task()
        assert task.categories == []

    def test_categories_with_values(self) -> None:
        task = self._make_task(categories=["Work", "Urgent"])
        assert task.categories == ["Work", "Urgent"]

    def test_etag_optional(self) -> None:
        task = self._make_task(etag='W/"abc"')
        assert task.etag == 'W/"abc"'

    def test_importance_high(self) -> None:
        task = self._make_task(importance="high")
        assert task.importance == TaskImportance.HIGH

    def test_status_enum_value(self) -> None:
        task = self._make_task(status=TaskStatus.DEFERRED)
        assert task.status == TaskStatus.DEFERRED

    def test_model_dump_round_trip(self) -> None:
        now = datetime.now(UTC)
        original = self._make_task(
            due_at=now,
            etag='W/"123"',
            categories=["Green"],
        )
        data = original.model_dump()
        restored = Task(**data)
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.due_at == original.due_at
        assert restored.etag == original.etag
        assert restored.categories == original.categories

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            Task(id="only-id")  # type: ignore[call-arg]

    def test_missing_title(self) -> None:
        with pytest.raises(ValidationError):
            Task(id="task-1", listId="list-1")  # type: ignore[call-arg]
