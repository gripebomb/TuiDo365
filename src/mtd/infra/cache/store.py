"""SQLite cache repository for local task and list storage.

Stores serialized domain models so the application can fall back to
cached data when Microsoft Graph is unreachable.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from mtd.domain.models import Task, TaskList
from mtd.infra.config.paths import cache_db_file

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS lists (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    list_id TEXT NOT NULL,
    data TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_list_id ON tasks(list_id);

CREATE TABLE IF NOT EXISTS sync_meta (
    key TEXT PRIMARY KEY,
    synced_at TEXT NOT NULL
);
"""


class CacheRepository:
    """Local SQLite cache for task lists and tasks."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or cache_db_file()
        self._ensure_db()

    def _ensure_db(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            conn.executescript(_SCHEMA)

    def _now(self) -> datetime:
        return datetime.now(UTC)

    # ── lists ────────────────────────────────────────────────────────

    def save_lists(self, lists: list[TaskList]) -> None:
        """Persist task lists, replacing any previous cache."""
        now = self._now().isoformat()
        with sqlite3.connect(self._path) as conn:
            conn.execute("DELETE FROM lists")
            conn.executemany(
                "INSERT INTO lists (id, data, synced_at) VALUES (?, ?, ?)",
                [(lst.id, lst.model_dump_json(), now) for lst in lists],
            )
            conn.execute(
                "INSERT OR REPLACE INTO sync_meta (key, synced_at) VALUES (?, ?)",
                ("lists", now),
            )
        logger.debug("Cached %d lists", len(lists))

    def get_lists(self) -> list[TaskList] | None:
        """Return cached lists or ``None`` when the cache is empty."""
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute("SELECT data FROM lists").fetchall()
        if not rows:
            return None
        return [TaskList.model_validate_json(row[0]) for row in rows]

    def get_lists_synced_at(self) -> datetime | None:
        """Return the timestamp when lists were last cached."""
        return self._get_synced_at("lists")

    # ── tasks ────────────────────────────────────────────────────────

    def save_tasks(self, list_id: str, tasks: list[Task]) -> None:
        """Persist tasks for a single list, replacing previous cache for that list."""
        now = self._now().isoformat()
        with sqlite3.connect(self._path) as conn:
            conn.execute("DELETE FROM tasks WHERE list_id = ?", (list_id,))
            conn.executemany(
                "INSERT INTO tasks (id, list_id, data, synced_at) VALUES (?, ?, ?, ?)",
                [(t.id, list_id, t.model_dump_json(), now) for t in tasks],
            )
            conn.execute(
                "INSERT OR REPLACE INTO sync_meta (key, synced_at) VALUES (?, ?)",
                (f"tasks:{list_id}", now),
            )
        logger.debug("Cached %d tasks for list %s", len(tasks), list_id)

    def get_tasks(self, list_id: str) -> list[Task] | None:
        """Return cached tasks for *list_id* or ``None`` when empty."""
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute("SELECT data FROM tasks WHERE list_id = ?", (list_id,)).fetchall()
        if not rows:
            return None
        return [Task.model_validate_json(row[0]) for row in rows]

    def get_tasks_synced_at(self, list_id: str) -> datetime | None:
        """Return the timestamp when tasks for *list_id* were last cached."""
        return self._get_synced_at(f"tasks:{list_id}")

    # ── helpers ──────────────────────────────────────────────────────

    def _get_synced_at(self, key: str) -> datetime | None:
        with sqlite3.connect(self._path) as conn:
            row = conn.execute("SELECT synced_at FROM sync_meta WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return datetime.fromisoformat(row[0])

    def clear(self) -> None:
        """Remove all cached data."""
        with sqlite3.connect(self._path) as conn:
            conn.execute("DELETE FROM lists")
            conn.execute("DELETE FROM tasks")
            conn.execute("DELETE FROM sync_meta")
        logger.debug("Cache cleared")
