"""Tests for AITabletop SDK client module."""
from unittest.mock import Mock, patch

import pytest

from aitabletop_sdk.agents.random_agent import RandomAgent
from aitabletop_sdk.client import DEFAULT_USER_AGENT, AITabletopClient
from aitabletop_sdk.exceptions import (
    AITabletopError,
    AuthenticationError,
    InsufficientFundsError,
    RateLimitError,
)
from aitabletop_sdk.exceptions import (
    ConnectionError as AITabletopConnectionError,
)

TEST_API_KEY = "at_test_abcdef1234567890"
TEST_BASE_URL = "https://api.example.com"


def make_client(**kwargs):
    """Create a client with test defaults."""
    kwargs.setdefault("api_key", TEST_API_KEY)
    kwargs.setdefault("base_url", TEST_BASE_URL)
    return AITabletopClient(**kwargs)


def make_response(status_code, json_data=None):
    """Create a mock HTTP response."""
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=json_data if json_data is not None else {})
    return response


class TestClientAuthHeaders:
    """Tests for authentication header construction."""

    def test_api_key_header_set_from_argument(self):
        """Test that the X-API-Key header is built from the api_key argument."""
        with make_client() as client:
            assert client._client.headers["X-API-Key"] == TEST_API_KEY

    def test_default_headers_set(self):
        """Test that Content-Type and User-Agent headers are set."""
        with make_client() as client:
            assert client._client.headers["Content-Type"] == "application/json"
            assert client._client.headers["User-Agent"] == DEFAULT_USER_AGENT

    def test_api_key_read_from_environment(self, monkeypatch):
        """Test that the API key falls back to AITABLETOP_API_KEY env var."""
        monkeypatch.setenv("AITABLETOP_API_KEY", TEST_API_KEY)
        with AITabletopClient(base_url=TEST_BASE_URL) as client:
            assert client._client.headers["X-API-Key"] == TEST_API_KEY

    def test_missing_api_key_raises(self, monkeypatch):
        """Test that a missing API key raises AuthenticationError."""
        monkeypatch.delenv("AITABLETOP_API_KEY", raising=False)
        with pytest.raises(AuthenticationError):
            AITabletopClient(base_url=TEST_BASE_URL)


class TestClientConfiguration:
    """Tests for client configuration validation."""

    def test_invalid_timeout_raises(self):
        """Test that a negative timeout raises AITabletopError."""
        with pytest.raises(AITabletopError):
            make_client(timeout=-5.0)

    def test_invalid_max_retries_raises(self):
        """Test that a negative max_retries raises AITabletopError."""
        with pytest.raises(AITabletopError):
            make_client(max_retries=-1)

    def test_ws_url_derived_from_https_base_url(self):
        """Test that the WebSocket URL is derived from the HTTP base URL."""
        with make_client() as client:
            assert client.ws_base_url == "wss://api.example.com"


class TestRegisterAgent:
    """Tests for register_agent method."""

    def test_register_agent_success(self):
        """Test successful agent registration."""
        response = make_response(
            201,
            {
                "id": "agent-123",
                "name": "MyBot",
                "game_type": "chess",
                "created_at": "2026-01-01T00:00:00Z",
            },
        )
        with make_client() as client:
            with patch.object(client._client, "post", return_value=response) as mock_post:
                result = client.register_agent("MyBot", "chess")

        mock_post.assert_called_once_with(
            "/api/v1/players/",
            json={"name": "MyBot", "game_type": "chess"},
        )
        assert result["agent_id"] == "agent-123"
        assert result["name"] == "MyBot"
        assert result["game_type"] == "chess"
        assert result["created_at"] == "2026-01-01T00:00:00Z"

    def test_register_agent_invalid_name_raises(self):
        """Test that an invalid agent name raises before any HTTP call."""
        with make_client() as client:
            with patch.object(client._client, "post") as mock_post:
                with pytest.raises(AITabletopError):
                    client.register_agent("", "chess")
        mock_post.assert_not_called()

    def test_register_agent_invalid_game_type_raises(self):
        """Test that an unsupported game type raises before any HTTP call."""
        with make_client() as client:
            with patch.object(client._client, "post") as mock_post:
                with pytest.raises(AITabletopError):
                    client.register_agent("MyBot", "checkers")
        mock_post.assert_not_called()

    def test_register_agent_authentication_error(self):
        """Test that a 401 response raises AuthenticationError."""
        response = make_response(401, {"detail": "Invalid API key"})
        with make_client() as client:
            with patch.object(client._client, "post", return_value=response):
                with pytest.raises(AuthenticationError) as exc_info:
                    client.register_agent("MyBot", "chess")
        assert "Invalid API key" in str(exc_info.value)

    def test_register_agent_rate_limit_error(self):
        """Test that a 429 response raises RateLimitError."""
        response = make_response(429, {"detail": "Too many requests"})
        with make_client() as client:
            with patch.object(client._client, "post", return_value=response):
                with pytest.raises(RateLimitError):
                    client.register_agent("MyBot", "chess")


class TestJoinQueue:
    """Tests for join_queue method."""

    def test_join_queue_insufficient_funds(self):
        """Test that a 402 response raises InsufficientFundsError."""
        response = make_response(402, {"detail": "Wallet balance too low"})
        with make_client() as client:
            with patch.object(client._client, "post", return_value=response):
                with pytest.raises(InsufficientFundsError):
                    client.join_queue("agent-123", "chess")


class TestPlayMatchRetries:
    """Tests for WebSocket connection retry behavior in play_match."""

    def test_play_match_retries_then_raises_connection_error(self):
        """Test that connection failures are retried max_retries times."""
        with make_client(max_retries=3, retry_delay=0.001) as client:
            with patch(
                "aitabletop_sdk.client.websockets.connect",
                side_effect=OSError("connection refused"),
            ) as mock_connect:
                with pytest.raises(AITabletopConnectionError) as exc_info:
                    client.play_match("match-test123", RandomAgent(seed=1))

        assert mock_connect.call_count == 3
        assert "after 3 attempts" in str(exc_info.value)
