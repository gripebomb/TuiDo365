"""XDG-compliant path resolution for TuiDo365.

Uses platformdirs to compute Linux-friendly paths for config, data,
cache, state, and log files. All paths follow the XDG Base Directory
Specification on Linux.
"""

from __future__ import annotations

from pathlib import Path

from platformdirs import PlatformDirs

_DIRS = PlatformDirs(appname="mtd", appauthor=False, roaming=False)


def config_dir() -> Path:
    """Return the config directory path (``~/.config/mtd``)."""
    return Path(_DIRS.user_config_dir)


def data_dir() -> Path:
    """Return the data directory path (``~/.local/share/mtd``)."""
    return Path(_DIRS.user_data_dir)


def cache_dir() -> Path:
    """Return the cache directory path (``~/.cache/mtd``)."""
    return Path(_DIRS.user_cache_dir)


def state_dir() -> Path:
    """Return the state directory path (``~/.local/state/mtd``)."""
    return Path(_DIRS.user_state_dir)


def config_file() -> Path:
    """Return the config file path (``~/.config/mtd/config.toml``)."""
    return config_dir() / "config.toml"


def token_cache_file() -> Path:
    """Return the token cache file path (``~/.local/share/mtd/token_cache.bin``)."""
    return data_dir() / "token_cache.bin"


def cache_db_file() -> Path:
    """Return the SQLite cache database path (``~/.local/share/mtd/cache.db``)."""
    return data_dir() / "cache.db"


def log_file() -> Path:
    """Return the log file path (``~/.local/state/mtd/app.log``)."""
    return state_dir() / "app.log"


def ensure_dirs() -> None:
    """Create all TuiDo365 directories that do not already exist.

    Safe to call multiple times.  Directories are created with default
    permissions; callers that need tighter restrictions (e.g. the token
    cache directory) should adjust permissions after creation.
    """
    for directory in (
        config_dir(),
        data_dir(),
        cache_dir(),
        state_dir(),
    ):
        directory.mkdir(parents=True, exist_ok=True)
