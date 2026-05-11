"""Tests for MtdSettings configuration loading and defaults."""

from __future__ import annotations

from pathlib import Path

import pytest

from mtd.infra.config.settings import CacheSettings, MtdSettings, UISettings

# ── UISettings ────────────────────────────────────────────────────────


class TestUISettings:
    """Tests for UISettings defaults and overrides."""

    def test_default_date_format(self) -> None:
        settings = UISettings()
        assert settings.date_format == "%Y-%m-%d"

    def test_default_list(self) -> None:
        settings = UISettings()
        assert settings.default_list == "Tasks"

    def test_default_theme(self) -> None:
        settings = UISettings()
        assert settings.theme == "dark"

    def test_custom_values(self) -> None:
        settings = UISettings(date_format="%d/%m/%Y", default_list="Work", theme="light")
        assert settings.date_format == "%d/%m/%Y"
        assert settings.default_list == "Work"
        assert settings.theme == "light"


# ── CacheSettings ─────────────────────────────────────────────────────


class TestCacheSettings:
    """Tests for CacheSettings defaults and overrides."""

    def test_defaults(self) -> None:
        settings = CacheSettings()
        assert settings.enabled is True
        assert settings.ttl_seconds == 300

    def test_custom_values(self) -> None:
        settings = CacheSettings(enabled=False, ttl_seconds=600)
        assert settings.enabled is False
        assert settings.ttl_seconds == 600


# ── MtdSettings defaults ─────────────────────────────────────────────


class TestMtdSettingsDefaults:
    """Tests for MtdSettings default values."""

    def test_default_tenant(self) -> None:
        settings = MtdSettings()
        assert settings.tenant == "common"

    def test_default_client_id_is_empty(self) -> None:
        settings = MtdSettings()
        assert settings.client_id == ""

    def test_default_scopes(self) -> None:
        settings = MtdSettings()
        assert settings.scopes == ["Tasks.ReadWrite", "offline_access"]

    def test_nested_ui_defaults(self) -> None:
        settings = MtdSettings()
        assert isinstance(settings.ui, UISettings)
        assert settings.ui.date_format == "%Y-%m-%d"
        assert settings.ui.default_list == "Tasks"
        assert settings.ui.theme == "dark"

    def test_nested_cache_defaults(self) -> None:
        settings = MtdSettings()
        assert isinstance(settings.cache, CacheSettings)
        assert settings.cache.enabled is True
        assert settings.cache.ttl_seconds == 300


# ── effective_scopes ─────────────────────────────────────────────────


class TestEffectiveScopes:
    """Tests for MtdSettings.effective_scopes."""

    def test_excludes_offline_access_from_api_calls(self) -> None:
        """MSAL adds offline_access automatically; don't duplicate it."""
        settings = MtdSettings()
        scopes = settings.effective_scopes()
        assert "offline_access" not in scopes
        assert "Tasks.ReadWrite" in scopes

    def test_filters_out_reserved_scopes(self) -> None:
        settings = MtdSettings(scopes=["Tasks.Read", "offline_access"])
        scopes = settings.effective_scopes()
        assert scopes == ["Tasks.Read"]

    def test_passes_through_non_reserved_scopes(self) -> None:
        settings = MtdSettings(scopes=["Tasks.Read"])
        scopes = settings.effective_scopes()
        assert scopes == ["Tasks.Read"]

    def test_does_not_mutate_original(self) -> None:
        settings = MtdSettings(scopes=["Tasks.Read", "offline_access"])
        original = list(settings.scopes)
        settings.effective_scopes()
        assert settings.scopes == original


# ── is_configured ────────────────────────────────────────────────────


class TestIsConfigured:
    """Tests for MtdSettings.is_configured."""

    def test_not_configured_when_empty(self) -> None:
        settings = MtdSettings()
        assert settings.is_configured() is False

    def test_configured_when_set(self) -> None:
        settings = MtdSettings(client_id="my-app-id")
        assert settings.is_configured() is True

    def test_not_configured_with_empty_string(self) -> None:
        settings = MtdSettings(client_id="")
        assert settings.is_configured() is False


# ── TOML loading ─────────────────────────────────────────────────────


class TestTomlLoading:
    """Tests for loading settings from TOML files."""

    def test_load_basic_toml(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text(
            'tenant = "my-tenant"\nclient_id = "app-id-123"\nscopes = ["Tasks.Read"]\n'
        )
        settings = MtdSettings.from_file(config)
        assert settings.tenant == "my-tenant"
        assert settings.client_id == "app-id-123"
        assert settings.scopes == ["Tasks.Read"]

    def test_partial_toml_uses_defaults(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text('client_id = "app-id-123"\n')
        settings = MtdSettings.from_file(config)
        assert settings.client_id == "app-id-123"
        assert settings.tenant == "common"

    def test_load_ui_section(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text(
            'client_id = "test"\n\n[ui]\ndate_format = "%d/%m/%Y"\ndefault_list = "Work"\n'
        )
        settings = MtdSettings.from_file(config)
        assert settings.ui.date_format == "%d/%m/%Y"
        assert settings.ui.default_list == "Work"

    def test_load_cache_section(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text('client_id = "test"\n\n[cache]\nenabled = false\nttl_seconds = 600\n')
        settings = MtdSettings.from_file(config)
        assert settings.cache.enabled is False
        assert settings.cache.ttl_seconds == 600

    def test_nonexistent_file_uses_defaults(self, tmp_path: Path) -> None:
        config = tmp_path / "nonexistent.toml"
        settings = MtdSettings.from_file(config)
        assert settings.tenant == "common"
        assert settings.client_id == ""

    def test_empty_toml_uses_defaults(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text("")
        settings = MtdSettings.from_file(config)
        assert settings.tenant == "common"
        assert settings.client_id == ""

    def test_full_config_round_trip(self, tmp_path: Path) -> None:
        config = tmp_path / "config.toml"
        config.write_text(
            'tenant = "organizations"\n'
            'client_id = "full-test-id"\n'
            'scopes = ["Tasks.ReadWrite", "offline_access"]\n\n'
            "[ui]\n"
            'date_format = "%m/%d/%Y"\n'
            'default_list = "Inbox"\n'
            'theme = "light"\n\n'
            "[cache]\n"
            "enabled = true\n"
            "ttl_seconds = 120\n"
        )
        settings = MtdSettings.from_file(config)
        assert settings.tenant == "organizations"
        assert settings.client_id == "full-test-id"
        assert settings.ui.date_format == "%m/%d/%Y"
        assert settings.ui.default_list == "Inbox"
        assert settings.ui.theme == "light"
        assert settings.cache.ttl_seconds == 120


# ── Environment variable overrides ───────────────────────────────────


class TestEnvVarOverrides:
    """Tests for environment variable configuration."""

    def test_tenant_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MTD_TENANT", "my-tenant")
        settings = MtdSettings()
        assert settings.tenant == "my-tenant"

    def test_client_id_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MTD_CLIENT_ID", "env-app-id")
        settings = MtdSettings()
        assert settings.client_id == "env-app-id"

    def test_nested_ui_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MTD_UI__DATE_FORMAT", "%d/%m/%Y")
        settings = MtdSettings()
        assert settings.ui.date_format == "%d/%m/%Y"

    def test_nested_cache_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MTD_CACHE__TTL_SECONDS", "900")
        settings = MtdSettings()
        assert settings.cache.ttl_seconds == 900

    def test_env_overrides_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MTD_TENANT", "override-tenant")
        settings = MtdSettings()
        assert settings.tenant == "override-tenant"
        # Other defaults should still be present
        assert settings.client_id == ""
