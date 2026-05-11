"""Tests for XDG-compliant path resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from mtd.infra.config.paths import (
    cache_db_file,
    cache_dir,
    config_dir,
    config_file,
    data_dir,
    ensure_dirs,
    log_file,
    state_dir,
    token_cache_file,
)


class TestPathFunctions:
    """Verify each path function returns the expected location."""

    def test_config_dir(self) -> None:
        result = config_dir()
        assert isinstance(result, Path)
        assert result.name == "mtd"
        parts = result.parts
        assert ".config" in parts

    def test_data_dir(self) -> None:
        result = data_dir()
        assert isinstance(result, Path)
        assert result.name == "mtd"
        parts = result.parts
        # platformdirs on Linux: ~/.local/share/mtd
        assert ".local" in parts or "share" in " ".join(parts)

    def test_cache_dir(self) -> None:
        result = cache_dir()
        assert isinstance(result, Path)
        assert result.name == "mtd"
        parts = result.parts
        assert ".cache" in parts

    def test_state_dir(self) -> None:
        result = state_dir()
        assert isinstance(result, Path)
        assert result.name == "mtd"
        parts = result.parts
        # platformdirs on Linux: ~/.local/state/mtd
        assert ".local" in parts

    def test_config_file(self) -> None:
        result = config_file()
        assert isinstance(result, Path)
        assert result.name == "config.toml"
        assert result == config_dir() / "config.toml"

    def test_token_cache_file(self) -> None:
        result = token_cache_file()
        assert isinstance(result, Path)
        assert result.name == "token_cache.bin"
        assert result == data_dir() / "token_cache.bin"

    def test_cache_db_file(self) -> None:
        result = cache_db_file()
        assert isinstance(result, Path)
        assert result.name == "cache.db"
        assert result == data_dir() / "cache.db"

    def test_log_file(self) -> None:
        result = log_file()
        assert isinstance(result, Path)
        assert result.name == "app.log"
        assert result == state_dir() / "app.log"


class TestEnsureDirs:
    """Verify that ensure_dirs creates the expected directory tree."""

    def test_creates_all_directories(self, tmp_path: Path) -> None:
        """ensure_dirs should create config, data, cache, and state dirs."""
        fake_config = tmp_path / "config" / "mtd"
        fake_data = tmp_path / "data" / "mtd"
        fake_cache = tmp_path / "cache" / "mtd"
        fake_state = tmp_path / "state" / "mtd"

        with (
            patch("mtd.infra.config.paths.config_dir", return_value=fake_config),
            patch("mtd.infra.config.paths.data_dir", return_value=fake_data),
            patch("mtd.infra.config.paths.cache_dir", return_value=fake_cache),
            patch("mtd.infra.config.paths.state_dir", return_value=fake_state),
        ):
            ensure_dirs()

        assert fake_config.is_dir()
        assert fake_data.is_dir()
        assert fake_cache.is_dir()
        assert fake_state.is_dir()

    def test_idempotent(self, tmp_path: Path) -> None:
        """Calling ensure_dirs multiple times should not raise."""
        fake_config = tmp_path / "config" / "mtd"
        fake_data = tmp_path / "data" / "mtd"
        fake_cache = tmp_path / "cache" / "mtd"
        fake_state = tmp_path / "state" / "mtd"

        with (
            patch("mtd.infra.config.paths.config_dir", return_value=fake_config),
            patch("mtd.infra.config.paths.data_dir", return_value=fake_data),
            patch("mtd.infra.config.paths.cache_dir", return_value=fake_cache),
            patch("mtd.infra.config.paths.state_dir", return_value=fake_state),
        ):
            ensure_dirs()
            ensure_dirs()  # second call should be safe

        assert fake_config.is_dir()
        assert fake_data.is_dir()
        assert fake_cache.is_dir()
        assert fake_state.is_dir()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """ensure_dirs should create intermediate parents that don't exist yet."""
        fake_config = tmp_path / "a" / "b" / "c" / "config"
        fake_data = tmp_path / "a" / "b" / "c" / "data"
        fake_cache = tmp_path / "a" / "b" / "c" / "cache"
        fake_state = tmp_path / "a" / "b" / "c" / "state"

        with (
            patch("mtd.infra.config.paths.config_dir", return_value=fake_config),
            patch("mtd.infra.config.paths.data_dir", return_value=fake_data),
            patch("mtd.infra.config.paths.cache_dir", return_value=fake_cache),
            patch("mtd.infra.config.paths.state_dir", return_value=fake_state),
        ):
            ensure_dirs()

        assert fake_config.is_dir()
        assert fake_data.is_dir()
        assert fake_cache.is_dir()
        assert fake_state.is_dir()
