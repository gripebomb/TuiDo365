"""Tests for the application auth service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from mtd.app.services.auth_service import AuthService, DeviceFlowInfo
from mtd.domain.errors import AuthError


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def service(mock_client):
    return AuthService(mock_client)


class TestInitiateLogin:
    """Verify login initiation."""

    def test_returns_device_flow_info(self, service: AuthService, mock_client: MagicMock) -> None:
        mock_client.initiate_device_flow.return_value = {
            "user_code": "ABC123",
            "message": "Go to example.com and enter ABC123",
            "verification_uri": "https://example.com",
            "expires_in": 900,
        }
        info = service.initiate_login()
        assert isinstance(info, DeviceFlowInfo)
        assert info.user_code == "ABC123"
        assert info.message == "Go to example.com and enter ABC123"
        assert info.verification_uri == "https://example.com"
        assert info.flow["user_code"] == "ABC123"

    def test_calls_client_with_defaults(self, service: AuthService, mock_client: MagicMock) -> None:
        mock_client.initiate_device_flow.return_value = {"user_code": "X"}
        service.initiate_login()
        mock_client.initiate_device_flow.assert_called_once_with()


class TestCompleteLogin:
    """Verify login completion."""

    def test_returns_auth_result(self, service: AuthService, mock_client: MagicMock) -> None:
        mock_client.acquire_token_by_device_flow.return_value = {
            "access_token": "atoken",
            "id_token_claims": {"preferred_username": "user@example.com"},
        }
        result = service.complete_login({"user_code": "ABC"})
        assert result.access_token == "atoken"
        assert result.account_username == "user@example.com"

    def test_handles_missing_id_token_claims(
        self, service: AuthService, mock_client: MagicMock
    ) -> None:
        mock_client.acquire_token_by_device_flow.return_value = {
            "access_token": "atoken",
        }
        result = service.complete_login({"user_code": "ABC"})
        assert result.account_username is None

    def test_passes_flow_to_client(self, service: AuthService, mock_client: MagicMock) -> None:
        mock_client.acquire_token_by_device_flow.return_value = {"access_token": "atoken"}
        flow = {"user_code": "ABC"}
        service.complete_login(flow)
        mock_client.acquire_token_by_device_flow.assert_called_once_with(flow)


class TestEnsureToken:
    """Verify token retrieval."""

    def test_returns_access_token(self, service: AuthService, mock_client: MagicMock) -> None:
        mock_client.get_token.return_value = {"access_token": "secret"}
        token = service.ensure_token()
        assert token == "secret"

    def test_raises_when_not_authenticated(
        self, service: AuthService, mock_client: MagicMock
    ) -> None:
        mock_client.get_token.return_value = None
        with pytest.raises(AuthError, match="mtd login"):
            service.ensure_token()


class TestLogout:
    """Verify logout."""

    def test_delegates_to_client(self, service: AuthService, mock_client: MagicMock) -> None:
        service.logout()
        mock_client.remove_all_accounts.assert_called_once_with()
