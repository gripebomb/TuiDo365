"""Tests for CLI authentication commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mtd.cli.app import app
from mtd.domain.errors import AuthDeniedError, AuthError

runner = CliRunner()


@pytest.fixture
def mock_auth_service():
    return MagicMock()


class TestLogin:
    """Verify ``mtd login`` behavior."""

    def test_success(self, mock_auth_service: MagicMock) -> None:
        mock_auth_service.initiate_login.return_value = MagicMock(
            user_code="ABC123",
            message="Go to https://microsoft.com/devicelogin and enter ABC123",
            verification_uri="https://microsoft.com/devicelogin",
            flow={"user_code": "ABC123"},
        )
        mock_auth_service.complete_login.return_value = MagicMock(
            access_token="token",
            account_username="test@example.com",
        )
        with patch("mtd.cli.auth_commands._auth_service", return_value=mock_auth_service):
            result = runner.invoke(app, ["login"])

        assert result.exit_code == 0
        assert "Go to https://microsoft.com/devicelogin" in result.output
        assert "Logged in as test@example.com" in result.output

    def test_handles_auth_error(self, mock_auth_service: MagicMock) -> None:
        mock_auth_service.initiate_login.return_value = MagicMock(
            message="msg",
            flow={},
        )
        mock_auth_service.complete_login.side_effect = AuthDeniedError("User cancelled")
        with patch("mtd.cli.auth_commands._auth_service", return_value=mock_auth_service):
            result = runner.invoke(app, ["login"])

        assert result.exit_code == 1
        assert "User cancelled" in result.output

    def test_handles_generic_error(self, mock_auth_service: MagicMock) -> None:
        mock_auth_service.initiate_login.side_effect = AuthError("Something broke")
        with patch("mtd.cli.auth_commands._auth_service", return_value=mock_auth_service):
            result = runner.invoke(app, ["login"])

        assert result.exit_code == 1
        assert "Something broke" in result.output

    def test_not_configured(self) -> None:
        with patch("mtd.cli.auth_commands.MtdSettings") as mock_settings_cls:
            mock_settings_cls.return_value.is_configured.return_value = False
            result = runner.invoke(app, ["login"])

        assert result.exit_code == 1
        assert "client_id is not configured" in result.output


class TestLogout:
    """Verify ``mtd logout`` behavior."""

    def test_success(self, mock_auth_service: MagicMock) -> None:
        with patch("mtd.cli.auth_commands._auth_service", return_value=mock_auth_service):
            result = runner.invoke(app, ["logout"])

        assert result.exit_code == 0
        assert "Logged out" in result.output
        mock_auth_service.logout.assert_called_once_with()

    def test_handles_error(self, mock_auth_service: MagicMock) -> None:
        mock_auth_service.logout.side_effect = AuthError("Cache locked")
        with patch("mtd.cli.auth_commands._auth_service", return_value=mock_auth_service):
            result = runner.invoke(app, ["logout"])

        assert result.exit_code == 1
        assert "Cache locked" in result.output
