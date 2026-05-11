"""Tests for domain error hierarchy."""

from __future__ import annotations

import pytest

from mtd.domain.errors import (
    AuthDeniedError,
    AuthError,
    BuiltInListError,
    CacheCorruptError,
    CacheError,
    CacheSchemaError,
    ConfigError,
    ConfigFileNotFoundError,
    ConfigParseError,
    DeviceCodeExpiredError,
    DeviceCodePollCancelledError,
    GraphError,
    GraphNetworkError,
    GraphNotFoundError,
    GraphPermissionError,
    GraphThrottlingError,
    MtdError,
    TokenRefreshError,
    ValidationError,
)

# ── Base error ───────────────────────────────────────────────────────


class TestMtdError:
    def test_message_stored(self) -> None:
        err = MtdError("something went wrong")
        assert err.message == "something went wrong"
        assert str(err) == "something went wrong"

    def test_detail_is_optional(self) -> None:
        err = MtdError("brief")
        assert err.detail is None

    def test_detail_stored(self) -> None:
        err = MtdError("brief", detail="long explanation here")
        assert err.detail == "long explanation here"

    def test_is_exception(self) -> None:
        with pytest.raises(MtdError, match="boom"):
            raise MtdError("boom")


# ── Auth errors ──────────────────────────────────────────────────────


class TestAuthErrors:
    def test_auth_error_inherits_mtd_error(self) -> None:
        assert issubclass(AuthError, MtdError)

    def test_device_code_expired_inherits_auth_error(self) -> None:
        assert issubclass(DeviceCodeExpiredError, AuthError)

    def test_device_code_poll_cancelled_inherits_auth_error(self) -> None:
        assert issubclass(DeviceCodePollCancelledError, AuthError)

    def test_auth_denied_inherits_auth_error(self) -> None:
        assert issubclass(AuthDeniedError, AuthError)

    def test_token_refresh_inherits_auth_error(self) -> None:
        assert issubclass(TokenRefreshError, AuthError)

    def test_auth_error_catches_all_subtypes(self) -> None:
        """Catching AuthError should catch every auth subtype."""
        for cls in (
            DeviceCodeExpiredError,
            DeviceCodePollCancelledError,
            AuthDeniedError,
            TokenRefreshError,
        ):
            with pytest.raises(AuthError):
                raise cls("auth failure")

    def test_auth_error_catches_mtd_error(self) -> None:
        """AuthError is also catchable as MtdError."""
        with pytest.raises(MtdError):
            raise AuthError("fail")


# ── Graph errors ─────────────────────────────────────────────────────


class TestGraphErrors:
    def test_graph_error_inherits_mtd_error(self) -> None:
        assert issubclass(GraphError, MtdError)

    def test_graph_error_fields(self) -> None:
        err = GraphError(
            "request failed",
            status_code=403,
            graph_code="ErrorAccessDenied",
            detail="Insufficient privileges",
        )
        assert err.message == "request failed"
        assert err.status_code == 403
        assert err.graph_code == "ErrorAccessDenied"
        assert err.detail == "Insufficient privileges"

    def test_graph_error_optional_fields_default_to_none(self) -> None:
        err = GraphError("request failed")
        assert err.status_code is None
        assert err.graph_code is None
        assert err.detail is None

    def test_permission_error_inherits_graph_error(self) -> None:
        assert issubclass(GraphPermissionError, GraphError)

    def test_not_found_error_inherits_graph_error(self) -> None:
        assert issubclass(GraphNotFoundError, GraphError)

    def test_network_error_inherits_graph_error(self) -> None:
        assert issubclass(GraphNetworkError, GraphError)

    def test_graph_error_catches_all_subtypes(self) -> None:
        for cls in (GraphPermissionError, GraphNotFoundError, GraphNetworkError):
            with pytest.raises(GraphError):
                raise cls("graph failure")

    def test_graph_error_stacks_as_mtd_error(self) -> None:
        with pytest.raises(MtdError):
            raise GraphPermissionError("denied")


class TestGraphThrottlingError:
    def test_inherits_graph_error(self) -> None:
        assert issubclass(GraphThrottlingError, GraphError)

    def test_default_message(self) -> None:
        err = GraphThrottlingError()
        assert err.message == "Request throttled by Microsoft Graph"

    def test_custom_message(self) -> None:
        err = GraphThrottlingError("slow down!")
        assert err.message == "slow down!"

    def test_retry_after_seconds(self) -> None:
        err = GraphThrottlingError(retry_after_seconds=30)
        assert err.retry_after_seconds == 30

    def test_retry_after_seconds_defaults_to_none(self) -> None:
        err = GraphThrottlingError()
        assert err.retry_after_seconds is None

    def test_carries_graph_error_fields(self) -> None:
        err = GraphThrottlingError(
            status_code=429,
            graph_code="ApplicationThrottled",
        )
        assert err.status_code == 429
        assert err.graph_code == "ApplicationThrottled"

    def test_catchable_as_graph_error(self) -> None:
        with pytest.raises(GraphError):
            raise GraphThrottlingError()


# ── Config errors ────────────────────────────────────────────────────


class TestConfigErrors:
    def test_config_error_inherits_mtd_error(self) -> None:
        assert issubclass(ConfigError, MtdError)

    def test_config_file_not_found_inherits_config_error(self) -> None:
        assert issubclass(ConfigFileNotFoundError, ConfigError)

    def test_config_parse_error_inherits_config_error(self) -> None:
        assert issubclass(ConfigParseError, ConfigError)

    def test_config_hierarchy_catchable(self) -> None:
        with pytest.raises(ConfigError):
            raise ConfigFileNotFoundError("missing")
        with pytest.raises(ConfigError):
            raise ConfigParseError("bad toml")


# ── Cache errors ─────────────────────────────────────────────────────


class TestCacheErrors:
    def test_cache_error_inherits_mtd_error(self) -> None:
        assert issubclass(CacheError, MtdError)

    def test_cache_schema_error_inherits_cache_error(self) -> None:
        assert issubclass(CacheSchemaError, CacheError)

    def test_cache_corrupt_error_inherits_cache_error(self) -> None:
        assert issubclass(CacheCorruptError, CacheError)

    def test_cache_hierarchy_catchable(self) -> None:
        with pytest.raises(CacheError):
            raise CacheSchemaError("wrong version")
        with pytest.raises(CacheError):
            raise CacheCorruptError("unreadable")


# ── Domain rule errors ──────────────────────────────────────────────


class TestBuiltInListError:
    def test_inherits_mtd_error(self) -> None:
        assert issubclass(BuiltInListError, MtdError)

    def test_message_includes_list_and_operation(self) -> None:
        err = BuiltInListError(list_name="Flagged Emails", operation="delete")
        assert "Flagged Emails" in err.message
        assert "delete" in err.message

    def test_detail_stored(self) -> None:
        err = BuiltInListError(list_name="Tasks", operation="rename")
        assert err.detail is not None
        assert "Tasks" in err.detail
        assert "rename" in err.detail

    def test_fields_accessible(self) -> None:
        err = BuiltInListError(list_name="Flagged Emails", operation="delete")
        assert err.list_name == "Flagged Emails"
        assert err.operation == "delete"

    def test_catchable_as_mtd_error(self) -> None:
        with pytest.raises(MtdError):
            raise BuiltInListError(list_name="Tasks", operation="delete")


class TestValidationError:
    def test_inherits_mtd_error(self) -> None:
        assert issubclass(ValidationError, MtdError)

    def test_field_stored(self) -> None:
        err = ValidationError("invalid value", field="due_date")
        assert err.field == "due_date"

    def test_field_defaults_to_none(self) -> None:
        err = ValidationError("invalid input")
        assert err.field is None

    def test_detail_stored(self) -> None:
        err = ValidationError("bad date", detail="Expected YYYY-MM-DD format")
        assert err.detail == "Expected YYYY-MM-DD format"

    def test_catchable_as_mtd_error(self) -> None:
        with pytest.raises(MtdError):
            raise ValidationError("bad input")
