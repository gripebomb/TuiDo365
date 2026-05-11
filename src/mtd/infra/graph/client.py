"""Base HTTP client for Microsoft Graph.

Wraps :mod:`httpx` with bearer-token injection, base-URL handling, and
mapping of HTTP status codes to domain exceptions.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Callable
from typing import Any, cast

import httpx

from mtd.domain.errors import (
    GraphError,
    GraphNetworkError,
    GraphNotFoundError,
    GraphPermissionError,
    GraphThrottlingError,
)

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://graph.microsoft.com/v1.0"
_DEFAULT_TIMEOUT = httpx.Timeout(30.0)


class GraphClient:
    """Small typed wrapper around the Microsoft Graph API.

    Args:
        token_provider: Callable that returns a valid bearer token string.
        base_url: Graph API base URL. Defaults to v1.0.
        timeout: Request timeout. Defaults to 30 seconds.
    """

    def __init__(
        self,
        token_provider: Callable[[], str],
        base_url: str = _DEFAULT_BASE_URL,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self._token_provider = token_provider
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout or _DEFAULT_TIMEOUT)

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Send an HTTP request to Graph and return the JSON body.

        Raises:
            GraphPermissionError: On HTTP 403.
            GraphNotFoundError: On HTTP 404.
            GraphThrottlingError: On HTTP 429.
            GraphNetworkError: On network-level failures.
            GraphError: On other non-2xx responses.
        """
        url = f"{self._base_url}/{path.lstrip('/')}"
        token = self._token_provider()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        logger.debug("Graph %s %s", method, url)
        try:
            response = self._client.request(method, url, headers=headers, **kwargs)
        except httpx.NetworkError as exc:
            logger.warning("Graph network error: %s", exc)
            raise GraphNetworkError(f"Network error contacting Graph: {exc}") from exc
        except httpx.TimeoutException as exc:
            logger.warning("Graph timeout: %s", exc)
            raise GraphNetworkError(f"Timeout contacting Graph: {exc}") from exc

        if response.status_code == 403:
            raise GraphPermissionError(
                "Permission denied by Microsoft Graph.",
                status_code=403,
            )

        if response.status_code == 404:
            raise GraphNotFoundError(
                "Resource not found in Microsoft Graph.",
                status_code=404,
            )

        if response.status_code == 429:
            retry_after = None
            with contextlib.suppress(ValueError):
                retry_after = int(response.headers.get("Retry-After", "0"))
            raise GraphThrottlingError(
                retry_after_seconds=retry_after or None,
                status_code=429,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("Graph HTTP error %s: %s", exc.response.status_code, exc.response.text)
            raise GraphError(
                f"Microsoft Graph returned {exc.response.status_code}.",
                status_code=exc.response.status_code,
            ) from exc

        if response.status_code == 204 or not response.content:
            return {}

        return cast(dict[str, Any], response.json())

    def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience wrapper for GET requests."""
        return self.request("GET", path, **kwargs)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
