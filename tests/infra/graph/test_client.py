"""Tests for the Graph HTTP client."""

from __future__ import annotations

import httpx
import pytest
import respx

from mtd.domain.errors import (
    GraphError,
    GraphNetworkError,
    GraphNotFoundError,
    GraphPermissionError,
    GraphThrottlingError,
)
from mtd.infra.graph.client import GraphClient


def _token_provider() -> str:
    return "test-token"


@pytest.fixture
def client() -> GraphClient:
    return GraphClient(token_provider=_token_provider, base_url="https://graph.test/v1.0")


class TestGet:
    """Verify GET requests."""

    def test_returns_json(self, client: GraphClient) -> None:
        with respx.mock:
            route = respx.get("https://graph.test/v1.0/me/todo/lists").mock(
                return_value=httpx.Response(200, json={"value": [{"id": "1"}]})
            )
            result = client.get("/me/todo/lists")

        assert result == {"value": [{"id": "1"}]}
        assert route.called
        request = route.calls[0].request
        assert request.headers["Authorization"] == "Bearer test-token"

    def test_403_raises_permission_error(self, client: GraphClient) -> None:
        with respx.mock:
            respx.get("https://graph.test/v1.0/me/todo/lists").mock(
                return_value=httpx.Response(403, json={"error": {"code": "ErrorAccessDenied"}})
            )
            with pytest.raises(GraphPermissionError):
                client.get("/me/todo/lists")

    def test_404_raises_not_found(self, client: GraphClient) -> None:
        with respx.mock:
            respx.get("https://graph.test/v1.0/me/todo/lists/bad-id").mock(
                return_value=httpx.Response(404, json={"error": {"code": "ErrorItemNotFound"}})
            )
            with pytest.raises(GraphNotFoundError):
                client.get("/me/todo/lists/bad-id")

    def test_429_raises_throttling_with_retry_after(self, client: GraphClient) -> None:
        with respx.mock:
            respx.get("https://graph.test/v1.0/me/todo/lists").mock(
                return_value=httpx.Response(429, headers={"Retry-After": "42"})
            )
            with pytest.raises(GraphThrottlingError) as exc_info:
                client.get("/me/todo/lists")

        assert exc_info.value.retry_after_seconds == 42

    def test_429_without_retry_after(self, client: GraphClient) -> None:
        with respx.mock:
            respx.get("https://graph.test/v1.0/me/todo/lists").mock(
                return_value=httpx.Response(429)
            )
            with pytest.raises(GraphThrottlingError) as exc_info:
                client.get("/me/todo/lists")

        assert exc_info.value.retry_after_seconds is None

    def test_500_raises_graph_error(self, client: GraphClient) -> None:
        with respx.mock:
            respx.get("https://graph.test/v1.0/me/todo/lists").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )
            with pytest.raises(GraphError) as exc_info:
                client.get("/me/todo/lists")

        assert exc_info.value.status_code == 500

    def test_network_error(self, client: GraphClient) -> None:
        with respx.mock:
            respx.get("https://graph.test/v1.0/me/todo/lists").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            with pytest.raises(GraphNetworkError, match="Connection refused"):
                client.get("/me/todo/lists")

    def test_timeout_error(self, client: GraphClient) -> None:
        with respx.mock:
            respx.get("https://graph.test/v1.0/me/todo/lists").mock(
                side_effect=httpx.TimeoutException("Read timeout")
            )
            with pytest.raises(GraphNetworkError, match="Read timeout"):
                client.get("/me/todo/lists")


class TestRequestMethod:
    """Verify generic request method."""

    def test_post_returns_json(self, client: GraphClient) -> None:
        with respx.mock:
            route = respx.post("https://graph.test/v1.0/me/todo/lists/list-1/tasks").mock(
                return_value=httpx.Response(201, json={"id": "task-1", "title": "New"})
            )
            result = client.request("POST", "/me/todo/lists/list-1/tasks", json={"title": "New"})

        assert result["id"] == "task-1"
        assert route.called

    def test_delete_returns_empty_dict(self, client: GraphClient) -> None:
        with respx.mock:
            route = respx.delete("https://graph.test/v1.0/me/todo/lists/list-1/tasks/task-1").mock(
                return_value=httpx.Response(204)
            )
            result = client.request("DELETE", "/me/todo/lists/list-1/tasks/task-1")

        assert result == {}
        assert route.called
