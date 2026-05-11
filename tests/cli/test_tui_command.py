"""Tests for the CLI TUI command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mtd.cli.app import app

runner = CliRunner()


class TestTui:
    """Verify ``mtd tui`` behavior."""

    def test_not_configured(self) -> None:
        with patch("mtd.cli.tui_command.MtdSettings") as mock_settings_cls:
            mock_settings_cls.return_value.is_configured.return_value = False
            result = runner.invoke(app, ["tui"])

        assert result.exit_code == 1
        assert "client_id is not configured" in result.output

    def test_launches_app(self) -> None:
        mock_app = MagicMock()
        with patch("mtd.cli.tui_command.MtdSettings") as mock_settings_cls:
            mock_settings_cls.return_value.is_configured.return_value = True
            with patch("mtd.cli.tui_command.MtdApp", return_value=mock_app):
                result = runner.invoke(app, ["tui"])

        assert result.exit_code == 0
        mock_app.run.assert_called_once()
