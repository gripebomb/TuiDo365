"""Application settings loaded from config files and environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from mtd.infra.config.paths import config_file


class UISettings(BaseModel):
    """User interface preferences."""

    date_format: str = "%Y-%m-%d"
    default_list: str = "Tasks"
    theme: str = "dark"


class CacheSettings(BaseModel):
    """Cache behavior configuration."""

    enabled: bool = True
    ttl_seconds: int = 300


class MtdSettings(BaseSettings):
    """Top-level application settings.

    Reads configuration from (in priority order):
      1. Environment variables prefixed with ``MTD_``
      2. ``~/.config/mtd/config.toml``
      3. Built-in defaults
    """

    model_config = SettingsConfigDict(
        env_prefix="MTD_",
        env_nested_delimiter="__",
        toml_file=config_file(),
    )

    tenant: str = "common"
    client_id: str = ""
    scopes: list[str] = Field(default_factory=lambda: ["Tasks.ReadWrite", "offline_access"])

    ui: UISettings = Field(default_factory=UISettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Add TOML file as a settings source with lower priority than env vars."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    @classmethod
    def from_file(cls, path: Path) -> MtdSettings:
        """Load settings from an explicit TOML file path.

        Useful for testing or for commands that need to point at a specific config.
        """
        settings_type = type(
            "_MtdSettingsFromFile",
            (cls,),
            {
                "model_config": SettingsConfigDict(
                    env_prefix="MTD_",
                    env_nested_delimiter="__",
                    toml_file=path,
                ),
            },
        )
        return settings_type()  # type: ignore[return-value,no-any-return]

    def effective_scopes(self) -> list[str]:
        """Return scopes for API calls (MSAL adds offline_access automatically)."""
        return [s for s in self.scopes if s != "offline_access"]

    def is_configured(self) -> bool:
        """Return True when the minimal required fields are present."""
        return bool(self.client_id)
