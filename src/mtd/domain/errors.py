"""Domain-specific errors for TuiDo365.

All application errors inherit from MtdError so callers can catch
at the granularity they need.
"""

from __future__ import annotations


class MtdError(Exception):
    """Base error for all TuiDo365 errors."""

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


# ── Auth errors ──────────────────────────────────────────────────────


class AuthError(MtdError):
    """Authentication or token acquisition failure."""


class DeviceCodeExpiredError(AuthError):
    """The device-code flow expired before the user completed sign-in."""


class DeviceCodePollCancelledError(AuthError):
    """Device-code polling was cancelled."""


class AuthDeniedError(AuthError):
    """The user or admin denied the auth request."""


class TokenRefreshError(AuthError):
    """Silent token refresh failed; re-login is required."""


# ── Graph / API errors ──────────────────────────────────────────────


class GraphError(MtdError):
    """Error communicating with Microsoft Graph."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        graph_code: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.graph_code = graph_code
        super().__init__(message, detail=detail)


class GraphPermissionError(GraphError):
    """The calling principal lacks the required delegated permission."""


class GraphNotFoundError(GraphError):
    """The requested resource was not found."""


class GraphThrottlingError(GraphError):
    """Microsoft Graph is throttling requests."""

    def __init__(
        self,
        message: str = "Request throttled by Microsoft Graph",
        *,
        retry_after_seconds: int | None = None,
        **kwargs: object,
    ) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message, **kwargs)  # type: ignore[arg-type]


class GraphNetworkError(GraphError):
    """A network-level failure before Graph could respond."""


# ── Config errors ───────────────────────────────────────────────────


class ConfigError(MtdError):
    """Configuration is missing, unreadable, or invalid."""


class ConfigFileNotFoundError(ConfigError):
    """The config file was expected but does not exist."""


class ConfigParseError(ConfigError):
    """The config file could not be parsed."""


# ── Cache errors ────────────────────────────────────────────────────


class CacheError(MtdError):
    """Local cache / SQLite failure."""


class CacheSchemaError(CacheError):
    """The cache schema is missing or at an unsupported version."""


class CacheCorruptError(CacheError):
    """The cache data is unreadable or inconsistent."""


# ── Domain rule errors ──────────────────────────────────────────────


class BuiltInListError(MtdError):
    """Attempted an unsupported mutation on a built-in task list.

    Built-in lists (Flagged Emails, Tasks, etc.) may have restricted
    operations.  This error is raised before any Graph call is made.
    """

    def __init__(self, list_name: str, operation: str) -> None:
        self.list_name = list_name
        self.operation = operation
        super().__init__(
            f"Cannot {operation} on built-in list '{list_name}'",
            detail=f"Built-in list '{list_name}' does not support '{operation}'.",
        )


class ValidationError(MtdError):
    """User input failed validation rules."""

    def __init__(
        self, message: str, *, field: str | None = None, detail: str | None = None
    ) -> None:
        self.field = field
        super().__init__(message, detail=detail)
