"""Token cache persistence for MSAL.

Wraps :class:`msal.SerializableTokenCache` so that tokens are loaded from
and saved to the Linux user data path (``~/.local/share/mtd/token_cache.bin``).
"""

from __future__ import annotations

import logging
from pathlib import Path

from msal import SerializableTokenCache

from mtd.infra.config.paths import token_cache_file

logger = logging.getLogger(__name__)


class TokenCache:
    """Filesystem-backed MSAL token cache.

    Loads existing serialized cache data on instantiation and provides a
    :meth:`save` helper to persist changes after MSAL operations.
    """

    def __init__(self, cache_path: Path | None = None) -> None:
        self._path = cache_path or token_cache_file()
        self._cache = SerializableTokenCache()
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = self._path.read_text()
                self._cache.deserialize(data)
                logger.debug("Loaded token cache from %s", self._path)
            except Exception:
                logger.warning(
                    "Failed to load token cache from %s, starting fresh",
                    self._path,
                    exc_info=True,
                )
                self._cache = SerializableTokenCache()

    def save(self) -> None:
        """Persist the cache to disk if MSAL has marked it as dirty."""
        if not self._cache.has_state_changed:
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(self._cache.serialize())
            logger.debug("Saved token cache to %s", self._path)
        except Exception:
            logger.warning("Failed to save token cache to %s", self._path, exc_info=True)

    def get_msal_cache(self) -> SerializableTokenCache:
        """Return the underlying MSAL cache instance."""
        return self._cache
