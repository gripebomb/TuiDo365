"""Application-level authentication service.

Orchestrates the MSAL auth adapter and exposes thin, predictable use cases
for login, token retrieval, and logout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mtd.domain.errors import AuthError
from mtd.infra.auth.msal_client import MsalAuthClient


@dataclass
class DeviceFlowInfo:
    """User-facing information for a device-code login flow."""

    user_code: str
    message: str
    verification_uri: str
    flow: dict[str, Any]


@dataclass
class AuthResult:
    """Result of a completed authentication flow."""

    access_token: str
    account_username: str | None = None


class AuthService:
    """High-level authentication operations.

    Wraps :class:`MsalAuthClient` and adds application-level conveniences
    such as structured result objects and user-facing error messages.
    """

    def __init__(self, client: MsalAuthClient) -> None:
        self._client = client

    def initiate_login(self) -> DeviceFlowInfo:
        """Start a device-code login flow.

        Returns:
            :class:`DeviceFlowInfo` containing the user code and the URI
            the user must visit to complete authentication.
        """
        flow = self._client.initiate_device_flow()
        return DeviceFlowInfo(
            user_code=flow.get("user_code", ""),
            message=flow.get("message", ""),
            verification_uri=flow.get("verification_uri", ""),
            flow=flow,
        )

    def complete_login(self, flow: dict[str, Any]) -> AuthResult:
        """Complete a device-code login flow.

        This blocks until the user finishes authentication in their browser
        or the flow expires.

        Returns:
            :class:`AuthResult` with the acquired access token.
        """
        result = self._client.acquire_token_by_device_flow(flow)
        username: str | None = None
        id_claims = result.get("id_token_claims")
        if isinstance(id_claims, dict):
            username = id_claims.get("preferred_username")
        return AuthResult(
            access_token=result["access_token"],
            account_username=username,
        )

    def ensure_token(self) -> str:
        """Return a valid access token, refreshing from cache if possible.

        Raises:
            AuthError: When the user is not authenticated and no cached
                token can be refreshed.
        """
        result = self._client.get_token()
        if result is None:
            raise AuthError("Not authenticated. Run `mtd login` first.")
        return str(result["access_token"])

    def logout(self) -> None:
        """Remove all cached accounts and tokens."""
        self._client.remove_all_accounts()
