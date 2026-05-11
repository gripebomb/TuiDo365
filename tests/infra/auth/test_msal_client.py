"""Tests for the MSAL auth adapter."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mtd.domain.errors import (
    AuthDeniedError,
    AuthError,
    DeviceCodeExpiredError,
    TokenRefreshError,
)
from mtd.infra.auth.msal_client import MsalAuthClient
from mtd.infra.auth.token_cache import TokenCache
from mtd.infra.config.settings import MtdSettings


@pytest.fixture
def settings() -> MtdSettings:
    return MtdSettings(client_id="test-client-id", tenant="common")


@pytest.fixture
def token_cache(tmp_path) -> TokenCache:
    return TokenCache(cache_path=tmp_path / "cache.bin")


class TestInitiateDeviceFlow:
    """Verify device flow initiation."""

    def test_returns_flow_dict(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        with patch.object(
            client._app,
            "initiate_device_flow",
            return_value={
                "user_code": "ABC123",
                "message": "Go to https://microsoft.com/devicelogin and enter ABC123",
                "verification_uri": "https://microsoft.com/devicelogin",
                "expires_in": 900,
            },
        ) as mock_init:
            flow = client.initiate_device_flow()

        mock_init.assert_called_once_with(scopes=["Tasks.ReadWrite", "offline_access"])
        assert flow["user_code"] == "ABC123"

    def test_uses_custom_scopes(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        with patch.object(
            client._app,
            "initiate_device_flow",
            return_value={
                "user_code": "XYZ",
                "message": "msg",
            },
        ) as mock_init:
            client.initiate_device_flow(scopes=["Tasks.Read"])

        mock_init.assert_called_once_with(scopes=["Tasks.Read"])

    def test_raises_on_msal_error_key(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        with (
            patch.object(
                client._app,
                "initiate_device_flow",
                return_value={
                    "error": "invalid_request",
                    "error_description": "Bad request",
                },
            ),
            pytest.raises(AuthError, match="Bad request"),
        ):
            client.initiate_device_flow()

    def test_raises_on_exception(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        with (
            patch.object(client._app, "initiate_device_flow", side_effect=ValueError("boom")),
            pytest.raises(AuthError, match="boom"),
        ):
            client.initiate_device_flow()


class TestAcquireTokenByDeviceFlow:
    """Verify device flow completion."""

    def test_returns_token_dict(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        flow = {"user_code": "ABC", "device_code": "DEF"}
        with patch.object(
            client._app,
            "acquire_token_by_device_flow",
            return_value={
                "access_token": "secret-token",
                "token_type": "Bearer",
            },
        ) as mock_acquire:
            result = client.acquire_token_by_device_flow(flow)

        mock_acquire.assert_called_once_with(flow)
        assert result["access_token"] == "secret-token"

    def test_raises_expired_token(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        flow = {"user_code": "ABC"}
        with (
            patch.object(
                client._app,
                "acquire_token_by_device_flow",
                return_value={
                    "error": "expired_token",
                    "error_description": "The device code has expired",
                },
            ),
            pytest.raises(DeviceCodeExpiredError),
        ):
            client.acquire_token_by_device_flow(flow)

    def test_raises_auth_denied(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        flow = {"user_code": "ABC"}
        with (
            patch.object(
                client._app,
                "acquire_token_by_device_flow",
                return_value={
                    "error": "authorization_declined",
                    "error_description": "User declined",
                },
            ),
            pytest.raises(AuthDeniedError),
        ):
            client.acquire_token_by_device_flow(flow)

    def test_raises_access_denied(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        flow = {"user_code": "ABC"}
        with (
            patch.object(
                client._app,
                "acquire_token_by_device_flow",
                return_value={
                    "error": "access_denied",
                },
            ),
            pytest.raises(AuthDeniedError),
        ):
            client.acquire_token_by_device_flow(flow)

    def test_raises_auth_error_for_unknown(
        self, settings: MtdSettings, token_cache: TokenCache
    ) -> None:
        client = MsalAuthClient(settings, token_cache)
        flow = {"user_code": "ABC"}
        with (
            patch.object(
                client._app,
                "acquire_token_by_device_flow",
                return_value={
                    "error": "server_error",
                    "error_description": "Something went wrong",
                },
            ),
            pytest.raises(AuthError, match="Something went wrong"),
        ):
            client.acquire_token_by_device_flow(flow)

    def test_raises_on_exception(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        flow = {"user_code": "ABC"}
        with (
            patch.object(
                client._app,
                "acquire_token_by_device_flow",
                side_effect=RuntimeError("network"),
            ),
            pytest.raises(AuthError, match="network"),
        ):
            client.acquire_token_by_device_flow(flow)


class TestGetToken:
    """Verify silent token acquisition."""

    def test_returns_none_when_no_accounts(
        self, settings: MtdSettings, token_cache: TokenCache
    ) -> None:
        client = MsalAuthClient(settings, token_cache)
        with patch.object(client._app, "get_accounts", return_value=[]):
            result = client.get_token()
        assert result is None

    def test_returns_token_when_available(
        self, settings: MtdSettings, token_cache: TokenCache
    ) -> None:
        client = MsalAuthClient(settings, token_cache)
        account = {"username": "test@example.com"}
        with (
            patch.object(client._app, "get_accounts", return_value=[account]),
            patch.object(
                client._app,
                "acquire_token_silent",
                return_value={"access_token": "silent-token"},
            ) as mock_silent,
        ):
            result = client.get_token()

        mock_silent.assert_called_once_with(
            scopes=["Tasks.ReadWrite", "offline_access"],
            account=account,
        )
        assert result is not None
        assert result["access_token"] == "silent-token"

    def test_returns_none_when_silent_returns_none(
        self, settings: MtdSettings, token_cache: TokenCache
    ) -> None:
        client = MsalAuthClient(settings, token_cache)
        account = {"username": "test@example.com"}
        with (
            patch.object(client._app, "get_accounts", return_value=[account]),
            patch.object(client._app, "acquire_token_silent", return_value=None),
        ):
            result = client.get_token()
        assert result is None

    def test_raises_on_silent_exception(
        self, settings: MtdSettings, token_cache: TokenCache
    ) -> None:
        client = MsalAuthClient(settings, token_cache)
        account = {"username": "test@example.com"}
        with (
            patch.object(client._app, "get_accounts", return_value=[account]),
            patch.object(
                client._app,
                "acquire_token_silent",
                side_effect=ConnectionError("down"),
            ),
            pytest.raises(TokenRefreshError, match="down"),
        ):
            client.get_token()


class TestGetAccounts:
    """Verify account retrieval."""

    def test_returns_accounts(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        accounts = [{"username": "a@b.com"}]
        with patch.object(client._app, "get_accounts", return_value=accounts):
            assert client.get_accounts() == accounts


class TestRemoveAllAccounts:
    """Verify logout."""

    def test_removes_all_accounts(self, settings: MtdSettings, token_cache: TokenCache) -> None:
        client = MsalAuthClient(settings, token_cache)
        accounts = [{"username": "a@b.com"}, {"username": "c@d.com"}]
        with (
            patch.object(client._app, "get_accounts", return_value=accounts),
            patch.object(client._app, "remove_account") as mock_remove,
        ):
            client.remove_all_accounts()

        assert mock_remove.call_count == 2
