"""Tests for infra.logging_setup — sensitive data redaction and logger configuration."""

from __future__ import annotations

import logging
from pathlib import Path

from mtd.infra.logging_setup import SensitiveDataFilter, get_logger, setup_logging

# ---------------------------------------------------------------------------
# SensitiveDataFilter
# ---------------------------------------------------------------------------


class TestSensitiveDataFilter:
    """Verify that the filter redacts tokens, secrets, and auth headers."""

    def _make_record(self, msg: str, *args: object) -> logging.LogRecord:
        """Create a LogRecord with the given message and args."""
        record = logging.LogRecord(
            name="mtd.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=msg,
            args=args or None,
            exc_info=None,
        )
        return record

    def test_redacts_bearer_token(self) -> None:
        filt = SensitiveDataFilter()
        result = filt._redact(
            "Authorization: bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123def456"
        )
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert "***REDACTED***" in result

    def test_redacts_authorization_header(self) -> None:
        filt = SensitiveDataFilter()
        result = filt._redact("authorization: Bearer my-secret-token-12345")
        assert "my-secret-token-12345" not in result
        assert "***REDACTED***" in result

    def test_redacts_access_token_field(self) -> None:
        filt = SensitiveDataFilter()
        result = filt._redact('{"access_token": "super-secret-token-value"}')
        assert "super-secret-token-value" not in result
        assert "***REDACTED***" in result

    def test_redacts_refresh_token_field(self) -> None:
        filt = SensitiveDataFilter()
        result = filt._redact('refresh_token="abc123xyz789"')
        assert "abc123xyz789" not in result
        assert "***REDACTED***" in result

    def test_redacts_id_token_field(self) -> None:
        filt = SensitiveDataFilter()
        result = filt._redact("id_token: some-jwt-value-here")
        assert "some-jwt-value-here" not in result
        assert "***REDACTED***" in result

    def test_redacts_client_secret(self) -> None:
        filt = SensitiveDataFilter()
        result = filt._redact('client_secret="my-client-secret-123"')
        assert "my-client-secret-123" not in result
        assert "***REDACTED***" in result

    def test_redacts_password_field(self) -> None:
        filt = SensitiveDataFilter()
        result = filt._redact("password=hunter2")
        assert "hunter2" not in result
        assert "***REDACTED***" in result

    def test_redacts_jwt_pattern(self) -> None:
        filt = SensitiveDataFilter()
        jwt = (
            "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        result = filt._redact(f"Got token: {jwt}")
        assert "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "***REDACTED_JWT***" in result

    def test_does_not_redact_normal_messages(self) -> None:
        filt = SensitiveDataFilter()
        msg = "Successfully listed 5 task lists for user"
        result = filt._redact(msg)
        assert result == msg

    def test_filter_returns_true(self) -> None:
        """The filter should always return True (does not suppress records)."""
        filt = SensitiveDataFilter()
        record = self._make_record("Normal message")
        assert filt.filter(record) is True

    def test_filter_redacts_record_msg(self) -> None:
        filt = SensitiveDataFilter()
        record = self._make_record("access_token: my-secret-token-abc123")
        filt.filter(record)
        assert "my-secret-token-abc123" not in record.getMessage()

    def test_filter_redacts_tuple_args(self) -> None:
        filt = SensitiveDataFilter()
        record = self._make_record("Response: %s", "access_token=my-secret-token-abc123")
        filt.filter(record)
        assert "my-secret-token-abc123" not in str(record.args)

    def test_filter_redacts_dict_args(self) -> None:
        filt = SensitiveDataFilter()
        record = self._make_record("Payload: %(data)s")
        record.args = {"data": "access_token=my-secret-token-abc123"}
        filt.filter(record)
        assert "my-secret-token-abc123" not in str(record.args)


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    """Verify that setup_logging configures handlers correctly."""

    def test_returns_logger_named_mtd(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()
        logger = setup_logging(log_dir=tmp_path)
        assert logger.name == "mtd"

    def test_creates_log_file(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()

        logger = setup_logging(log_dir=tmp_path)
        logger.info("test message for file")

        # Flush handlers so content is written
        for handler in logger.handlers:
            handler.flush()

        log_file = tmp_path / "app.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert "test message for file" in content

    def test_does_not_add_duplicate_handlers(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()

        logger1 = setup_logging(log_dir=tmp_path)
        handler_count = len(logger1.handlers)
        logger2 = setup_logging(log_dir=tmp_path)
        assert len(logger2.handlers) == handler_count

    def test_file_handler_is_debug_level(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()

        logger = setup_logging(log_dir=tmp_path)
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.DEBUG

    def test_console_handler_is_warning_level(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()

        logger = setup_logging(log_dir=tmp_path)
        console_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1
        assert console_handlers[0].level == logging.WARNING

    def test_custom_console_level(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()

        logger = setup_logging(console_level=logging.ERROR, log_dir=tmp_path)
        console_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        assert console_handlers[0].level == logging.ERROR

    def test_handlers_have_sensitive_filter(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()

        logger = setup_logging(log_dir=tmp_path)
        for handler in logger.handlers:
            filters_of_type = [f for f in handler.filters if isinstance(f, SensitiveDataFilter)]
            assert len(filters_of_type) >= 1, f"Handler {handler} is missing SensitiveDataFilter"

    def test_redacts_sensitive_data_in_log_file(self, tmp_path: Path) -> None:
        root = logging.getLogger("mtd")
        root.handlers.clear()

        logger = setup_logging(log_dir=tmp_path)
        logger.info('Got access_token="super-secret-value-12345"')

        for handler in logger.handlers:
            handler.flush()

        log_file = tmp_path / "app.log"
        content = log_file.read_text()
        assert "super-secret-value-12345" not in content
        assert "***REDACTED***" in content

    def test_creates_log_directory_if_missing(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "nested" / "log" / "dir"
        root = logging.getLogger("mtd")
        root.handlers.clear()

        setup_logging(log_dir=log_dir)
        assert log_dir.exists()


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Verify that get_logger returns properly named child loggers."""

    def test_returns_child_logger(self) -> None:
        logger = get_logger("infra.graph.client")
        assert logger.name == "mtd.infra.graph.client"

    def test_returns_different_loggers_for_different_names(self) -> None:
        logger_a = get_logger("module_a")
        logger_b = get_logger("module_b")
        assert logger_a is not logger_b
        assert logger_a.name != logger_b.name

    def test_child_logger_propagates_to_parent(self) -> None:
        """Child loggers should propagate to the mtd root logger."""
        child = get_logger("some.child")
        assert child.propagate is True
        assert child.parent is not None
        assert child.parent.name == "mtd"
