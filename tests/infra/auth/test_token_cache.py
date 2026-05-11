"""Tests for token cache persistence."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from mtd.infra.auth.token_cache import TokenCache


class TestTokenCache:
    """Verify TokenCache loads, saves, and handles errors."""

    def test_creates_empty_cache_when_file_missing(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "missing.bin"
        tc = TokenCache(cache_path=cache_path)
        msal_cache = tc.get_msal_cache()
        assert msal_cache is not None
        # An empty cache has not changed
        assert not msal_cache.has_state_changed

    def test_loads_existing_cache(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "token_cache.bin"
        # Write a minimal serialized cache (MSAL JSON format)
        cache_path.write_text(
            '{"AccessToken": {}, "RefreshToken": {}, "IdToken": {},'
            ' "Account": {}, "AppMetadata": {}}'
        )
        tc = TokenCache(cache_path=cache_path)
        assert tc.get_msal_cache() is not None

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "nested" / "deep" / "token_cache.bin"
        tc = TokenCache(cache_path=cache_path)
        # Simulate MSAL marking cache as changed
        tc.get_msal_cache().add({})  # type: ignore[arg-type]
        tc.save()
        assert cache_path.exists()

    def test_save_noop_when_unchanged(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "token_cache.bin"
        tc = TokenCache(cache_path=cache_path)
        tc.save()
        assert not cache_path.exists()

    def test_load_failure_falls_back_to_empty(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "corrupt.bin"
        cache_path.write_text("not-valid-json{")
        tc = TokenCache(cache_path=cache_path)
        # Should not raise and should provide a usable cache
        assert tc.get_msal_cache() is not None

    def test_save_failure_does_not_raise(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "token_cache.bin"
        tc = TokenCache(cache_path=cache_path)
        tc.get_msal_cache().add({})  # type: ignore[arg-type]
        # Make the directory read-only to trigger a save failure
        with patch.object(Path, "write_text", side_effect=PermissionError("denied")):
            tc.save()  # should not raise
