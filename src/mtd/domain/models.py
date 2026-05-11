"""Domain models for Microsoft To Do entities.

These are project-owned models that the entire application works with.
Graph-specific payload shapes must be mapped into these models at the
infrastructure boundary and never leak above it.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TaskStatus(StrEnum):
    """Status of a task.

    Mirrors the Microsoft Graph ``taskStatus`` values.
    """

    NOT_STARTED = "notStarted"
    IN_PROGRESS = "inProgress"
    COMPLETED = "completed"
    WAITING_ON_OTHERS = "waitingOnOthers"
    DEFERRED = "deferred"


class TaskImportance(StrEnum):
    """Importance level of a task.

    Mirrors the Microsoft Graph ``importance`` values.
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class WellKnownListName(StrEnum):
    """Well-known list identifiers used by Microsoft To Do.

    Built-in lists have special mutation rules — for example, the
    default task list and the flagged-emails list should not be
    renamed or deleted.
    """

    NONE = "none"
    DEFAULT_LIST = "defaultList"
    FLAGGED_EMAILS = "flaggedEmails"
    UNKNOWN_FUTURE_VALUE = "unknownFutureValue"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TaskList(BaseModel):
    """A Microsoft To Do task list."""

    id: str
    display_name: str = Field(alias="displayName")
    wellknown_list_name: WellKnownListName = Field(
        default=WellKnownListName.NONE,
        alias="wellknownListName",
    )
    is_owner: bool = Field(default=True, alias="isOwner")
    is_shared: bool = Field(default=False, alias="isShared")

    model_config = {"populate_by_name": True}

    @property
    def is_builtin(self) -> bool:
        """Return ``True`` if this is a built-in list.

        Used to enforce mutation guardrails (no delete / rename on
        built-in lists).
        """
        return self.wellknown_list_name not in (
            WellKnownListName.NONE,
            WellKnownListName.UNKNOWN_FUTURE_VALUE,
        )


class TaskBody(BaseModel):
    """The body content of a task."""

    content: str = ""
    content_type: str = Field(default="text", alias="contentType")

    model_config = {"populate_by_name": True}


class Task(BaseModel):
    """A Microsoft To Do task."""

    id: str
    list_id: str = Field(alias="listId")
    title: str
    status: TaskStatus = Field(default=TaskStatus.NOT_STARTED)
    importance: TaskImportance = Field(default=TaskImportance.NORMAL)
    body: TaskBody | None = None
    due_at: datetime | None = Field(default=None, alias="dueDateTime")
    start_at: datetime | None = Field(default=None, alias="startDateTime")
    reminder_at: datetime | None = Field(default=None, alias="reminderDateTime")
    completed_at: datetime | None = Field(default=None, alias="completedDateTime")
    last_modified_at: datetime | None = Field(default=None, alias="lastModifiedDateTime")
    etag: str | None = None
    categories: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def is_completed(self) -> bool:
        """Return ``True`` when the task status is completed."""
        return self.status == TaskStatus.COMPLETED
