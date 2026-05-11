"""Structured logging setup with file and console handlers and sensitive data redaction."""

from __future__ import annotations

import logging
import re
from pathlib import Path

_DEFAULT_LOG_FILE = "app.log"
_LOGGER_NAME = "mtd"


class SensitiveDataFilter(logging.Filter):
    """Redacts tokens, secrets, and authorization headers from log records."""

    _PATTERNS: list[tuple[re.Pattern[str], str]] = [
        # Bearer tokens in headers or URLs
        (re.compile(r"(bearer\s+)[^\s,;\"']+", re.IGNORECASE), r"\1***REDACTED***"),
        # Authorization header values
        (
            re.compile(r"(authorization[\"']?\s*[:=]\s*[\"']?)[^\s,;\"']+", re.IGNORECASE),
            r"\1***REDACTED***",
        ),
        # Access/refresh/id token fields
        (
            re.compile(r"(access_token[\"']?\s*[:=]\s*[\"']?)[^\s,;\"']+", re.IGNORECASE),
            r"\1***REDACTED***",
        ),
        (
            re.compile(r"(refresh_token[\"']?\s*[:=]\s*[\"']?)[^\s,;\"']+", re.IGNORECASE),
            r"\1***REDACTED***",
        ),
        (
            re.compile(r"(id_token[\"']?\s*[:=]\s*[\"']?)[^\s,;\"']+", re.IGNORECASE),
            r"\1***REDACTED***",
        ),
        # Client secret fields
        (
            re.compile(r"(client_secret[\"']?\s*[:=]\s*[\"']?)[^\s,;\"']+", re.IGNORECASE),
            r"\1***REDACTED***",
        ),
        # Password key-value patterns
        (
            re.compile(r"(password[\"']?\s*[:=]\s*[\"']?)[^\s,;\"']+", re.IGNORECASE),
            r"\1***REDACTED***",
        ),
        # JWT-like strings (three base64url segments separated by dots)
        (
            re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
            "***REDACTED_JWT***",
        ),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from the log record message and args."""
        record.msg = self._redact(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact(str(a)) for a in record.args)
        return True

    @classmethod
    def _redact(cls, text: str) -> str:
        for pattern, replacement in cls._PATTERNS:
            text = pattern.sub(replacement, text)
        return text


class _MaxLevelFilter(logging.Filter):
    """Allows only log records at or below a maximum level."""

    def __init__(self, max_level: int) -> None:
        super().__init__()
        self._max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self._max_level


def setup_logging(
    *,
    level: int = logging.DEBUG,
    console_level: int = logging.WARNING,
    log_dir: Path | None = None,
) -> logging.Logger:
    """Configure structured logging for the application.

    Sets up two handlers on the ``mtd`` logger:

    - A file handler that captures DEBUG and above with detailed formatting.
    - A console handler that shows WARNING and above to the user.

    Both handlers are filtered through :class:`SensitiveDataFilter` to
    prevent tokens, secrets, and authorization headers from appearing in
    logs.

    Args:
        level: Minimum level for the file handler. Defaults to DEBUG.
        console_level: Minimum level shown on the console. Defaults to WARNING.
        log_dir: Directory for the log file. When *None*, uses
            ``~/.local/state/mtd``. The directory is created if it does not
            exist.

    Returns:
        The configured ``mtd`` logger instance.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    sensitive_filter = SensitiveDataFilter()

    # --- File handler ---
    if log_dir is None:
        log_dir = Path.home() / ".local" / "state" / "mtd"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / _DEFAULT_LOG_FILE

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.addFilter(sensitive_filter)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s %(filename)s:%(lineno)d  %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(file_handler)

    # --- Console handler (stderr) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.addFilter(sensitive_filter)
    console_handler.setFormatter(logging.Formatter(fmt="%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)

    logger.debug(
        "Logging initialized (file=%s, console_level=%s)",
        log_file,
        logging.getLevelName(console_level),
    )

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``mtd`` namespace.

    Use this in every module instead of ``logging.getLogger`` directly so
    that all loggers share the configured handlers and filters.

    Args:
        name: Dotted suffix appended to ``mtd``. For example,
            ``"infra.graph.client"`` produces ``mtd.infra.graph.client``.

    Returns:
        A logger descended from the ``mtd`` root logger.
    """
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
