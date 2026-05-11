"""MSAL authentication adapter.

Wraps :class:`msal.PublicClientApplication` behind a narrow project-owned
interface and maps MSAL result dicts and exceptions to domain errors.
"""

from __future__ import annotations

import logging
from typing import Any, cast

import msal

from mtd.domain.errors import (
    AuthDeniedError,
    AuthError,
    DeviceCodeExpiredError,
    DeviceCodePollCancelledError,
    TokenRefreshError,
)
from mtd.infra.auth.token_cache import TokenCache
from mtd.infra.config.settings import MtdSettings

logger = logging.getLogger(__name__)


class MsalAuthClient:
    """Thin wrapper around MSAL for device-code and silent token flows."""

    def __init__(
        self,
        settings: MtdSettings,
        token_cache: TokenCache | None = None,
    ) -> None:
        self._settings = settings
        self._token_cache = token_cache or TokenCache()
        self._app = self._build_app()

    def _build_app(self) -> msal.PublicClientApplication:
        authority = f"https://login.microsoftonline.com/{self._settings.tenant}"
        return msal.PublicClientApplication(
            client_id=self._settings.client_id,
            authority=authority,
            token_cache=self._token_cache.get_msal_cache(),
        )

    def initiate_device_flow(self, scopes: list[str] | None = None) -> dict[str, Any]:
        """Start a device-code flow.

        Returns a dict containing ``user_code``, ``message``,
        ``verification_uri``, and other MSAL flow metadata.

        Raises:
            AuthError: When the flow cannot be initiated.
        """
        effective_scopes = scopes or self._settings.effective_scopes()
        try:
            flow = self._app.initiate_device_flow(scopes=effective_scopes)
        except Exception as exc:
            logger.exception("Failed to initiate device flow")
            raise AuthError(f"Failed to initiate device flow: {exc}") from exc

        if "error" in flow:
            error_code = flow.get("error", "unknown")
            desc = flow.get("error_description", "Unknown error")
            logger.warning("MSAL initiate_device_flow error: %s - %s", error_code, desc)
            raise AuthError(f"Failed to initiate device flow: {desc}")

        logger.debug("Device flow initiated (expires_at=%s)", flow.get("expires_at"))
        return cast(dict[str, Any], flow)

    def acquire_token_by_device_flow(self, flow: dict[str, Any]) -> dict[str, Any]:
        """Complete a device-code flow.

        This method blocks until the user completes authentication in their
        browser or the flow expires.

        Returns:
            A dict containing ``access_token`` and related claims on success.

        Raises:
            DeviceCodeExpiredError: When the device code expires.
            AuthDeniedError: When the user or admin denies the request.
            AuthError: On any other authentication failure.
        """
        try:
            result = self._app.acquire_token_by_device_flow(flow)
        except Exception as exc:
            logger.exception("Device flow token acquisition failed")
            raise AuthError(f"Token acquisition failed: {exc}") from exc
        finally:
            # Always persist any cache mutations (even on error MSAL may
            # have written intermediate state).
            self._token_cache.save()

        return self._handle_result(result)

    def get_token(self, scopes: list[str] | None = None) -> dict[str, Any] | None:
        """Acquire a token silently from cache.

        Returns:
            Token dict on success, ``None`` when no cached account exists.

        Raises:
            TokenRefreshError: When silent refresh fails unexpectedly.
        """
        effective_scopes = scopes or self._settings.effective_scopes()
        accounts = self._app.get_accounts()
        if not accounts:
            return None

        try:
            result = self._app.acquire_token_silent(
                scopes=effective_scopes,
                account=accounts[0],
            )
        except Exception as exc:
            logger.exception("Silent token refresh failed")
            raise TokenRefreshError(f"Silent token refresh failed: {exc}") from exc

        if result is None:
            return None

        self._token_cache.save()
        return self._handle_result(result)

    def get_accounts(self) -> list[dict[str, Any]]:
        """Return cached accounts."""
        return cast(list[dict[str, Any]], self._app.get_accounts())

    def remove_all_accounts(self) -> None:
        """Remove all cached accounts (logout)."""
        for account in self._app.get_accounts():
            self._app.remove_account(account)
        self._token_cache.save()

    def _handle_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Map MSAL error responses to domain exceptions."""
        if "error" not in result:
            return result

        error = result.get("error", "unknown")
        desc = result.get("error_description", "")
        logger.warning("MSAL error: %s - %s", error, desc)

        if error == "authorization_pending":
            raise DeviceCodePollCancelledError(
                "User has not completed device-code authentication yet."
            )
        if error == "expired_token":
            raise DeviceCodeExpiredError("Device code flow expired before completion.")
        if error in ("authorization_declined", "access_denied"):
            raise AuthDeniedError("Authentication was denied by the user or administrator.")

        raise AuthError(f"Authentication failed: {desc or error}")
