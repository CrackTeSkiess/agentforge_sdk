"""Validators for AITabletop SDK input and response validation.

This module provides comprehensive validation for all SDK inputs,
API responses, and data integrity checks.
"""

from __future__ import annotations

import re
from typing import Any, Optional, Tuple

from aitabletop_sdk.exceptions import InvalidActionError, AITabletopError

# Supported game types
SUPPORTED_GAMES = frozenset({"chess", "go", "uno", "poker", "tarot", "san_juan", "qwixx"})

# API key format: at_live_<base64url_chars> or at_test_<base64url_chars>
API_KEY_PATTERN = re.compile(r"^at_(live|test)_[A-Za-z0-9_-]{16,}$")

# Agent name: alphanumeric, spaces, underscores, hyphens, 1-100 chars
AGENT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9 _-]{0,98}[a-zA-Z0-9]$|^[a-zA-Z0-9]$")

# Match ID format: match-<alphanumeric>
MATCH_ID_PATTERN = re.compile(r"^match-[A-Za-z0-9_-]+$")

# Agent ID format: <alphanumeric>
AGENT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# Queue ID format: queue-<alphanumeric>
QUEUE_ID_PATTERN = re.compile(r"^queue-[A-Za-z0-9_-]+$")

# Maximum values
MAX_AGENT_NAME_LENGTH = 100
MAX_MATCH_COST = 10000  # Maximum reasonable match cost
MAX_TIME_LIMIT_MS = 300000  # 5 minutes
MIN_TIME_LIMIT_MS = 100  # 100ms minimum
MAX_RETRY_ATTEMPTS = 10
MAX_TIMEOUT_SECONDS = 300  # 5 minutes
MAX_RATE_LIMIT_ATTEMPTS = 5


def validate_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """Validate API key format.

    Args:
        api_key: The API key to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
    """
    if not api_key:
        return False, "API key cannot be empty"

    if not isinstance(api_key, str):
        return False, "API key must be a string"

    if len(api_key) < 20:  # af_live_ (8) + 16 chars minimum
        return False, "API key is too short"

    if not API_KEY_PATTERN.match(api_key):
        return False, (
            "Invalid API key format. Expected format: at_live_xxxxxxxx or at_test_xxxxxxxx "
            "(at least 16 characters after prefix)"
        )

    return True, None


def validate_game_type(game_type: str) -> Tuple[bool, Optional[str]]:
    """Validate game type.

    Args:
        game_type: The game type to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not game_type:
        return False, "Game type cannot be empty"

    if not isinstance(game_type, str):
        return False, "Game type must be a string"

    if game_type not in SUPPORTED_GAMES:
        return False, f"Unsupported game type: '{game_type}'. Supported: {', '.join(sorted(SUPPORTED_GAMES))}"

    return True, None


def validate_agent_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate agent name format.

    Args:
        name: The agent name to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not name:
        return False, "Agent name cannot be empty"

    if not isinstance(name, str):
        return False, "Agent name must be a string"

    if len(name) > MAX_AGENT_NAME_LENGTH:
        return False, f"Agent name too long (max {MAX_AGENT_NAME_LENGTH} characters)"

    if len(name) < 1:
        return False, "Agent name must be at least 1 character"

    if not AGENT_NAME_PATTERN.match(name):
        return False, (
            "Invalid agent name format. Name must start and end with alphanumeric character, "
            "and can contain letters, numbers, spaces, underscores, and hyphens."
        )

    return True, None


def validate_match_id(match_id: str) -> Tuple[bool, Optional[str]]:
    """Validate match ID format.

    Args:
        match_id: The match ID to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not match_id:
        return False, "Match ID cannot be empty"

    if not isinstance(match_id, str):
        return False, "Match ID must be a string"

    if not MATCH_ID_PATTERN.match(match_id):
        return False, "Invalid match ID format. Expected format: match-xxxxxx"

    return True, None


def validate_agent_id(agent_id: str) -> Tuple[bool, Optional[str]]:
    """Validate agent ID format.

    Args:
        agent_id: The agent ID to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not agent_id:
        return False, "Agent ID cannot be empty"

    if not isinstance(agent_id, str):
        return False, "Agent ID must be a string"

    if not AGENT_ID_PATTERN.match(agent_id):
        return False, "Invalid agent ID format. Agent ID must be alphanumeric with underscores and hyphens."

    return True, None


def validate_queue_id(queue_id: str) -> Tuple[bool, Optional[str]]:
    """Validate queue ID format.

    Args:
        queue_id: The queue ID to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not queue_id:
        return False, "Queue ID cannot be empty"

    if not isinstance(queue_id, str):
        return False, "Queue ID must be a string"

    if not QUEUE_ID_PATTERN.match(queue_id):
        return False, "Invalid queue ID format. Expected format: queue-xxxxxx"

    return True, None


def validate_timeout(timeout: float) -> Tuple[bool, Optional[str]]:
    """Validate timeout value.

    Args:
        timeout: The timeout value in seconds.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(timeout, (int, float)):
        return False, "Timeout must be a number"

    if timeout <= 0:
        return False, "Timeout must be positive"

    if timeout > MAX_TIMEOUT_SECONDS:
        return False, f"Timeout too large (max {MAX_TIMEOUT_SECONDS} seconds)"

    return True, None


def validate_retry_count(retries: int) -> Tuple[bool, Optional[str]]:
    """Validate retry count.

    Args:
        retries: The number of retry attempts.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(retries, int):
        return False, "Retry count must be an integer"

    if retries < 0:
        return False, "Retry count cannot be negative"

    if retries > MAX_RETRY_ATTEMPTS:
        return False, f"Retry count too large (max {MAX_RETRY_ATTEMPTS})"

    return True, None


def validate_action(action: Any, game_type: str) -> Tuple[bool, Optional[str]]:
    """Validate action format.

    Args:
        action: The action to validate.
        game_type: The game type for context-specific validation.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if action is None:
        return False, "Action cannot be None"

    if not isinstance(action, dict):
        return False, "Action must be a dictionary"

    # Check for common action formats
    has_move = "move" in action
    has_action = "action" in action

    if not has_move and not has_action:
        return False, "Action must contain 'move' or 'action' key"

    # Validate move value if present
    if has_move:
        move = action["move"]
        if move is None:
            return False, "Move value cannot be None"

    return True, None


def validate_observation(observation: Any) -> Tuple[bool, Optional[str]]:
    """Validate observation format.

    Args:
        observation: The observation dict to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if observation is None:
        return False, "Observation cannot be None"

    if not isinstance(observation, dict):
        return False, "Observation must be a dictionary"

    return True, None


def validate_base_url(base_url: str) -> Tuple[bool, Optional[str]]:
    """Validate base URL format.

    Args:
        base_url: The base URL to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not base_url:
        return False, "Base URL cannot be empty"

    if not isinstance(base_url, str):
        return False, "Base URL must be a string"

    # Check for valid URL pattern
    if not base_url.startswith(("http://", "https://")):
        return False, "Base URL must start with http:// or https://"

    return True, None


def validate_match_cost(cost: int) -> Tuple[bool, Optional[str]]:
    """Validate match cost.

    Args:
        cost: The match cost in cents.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(cost, (int, float)):
        return False, "Match cost must be a number"

    if cost < 0:
        return False, "Match cost cannot be negative"

    if cost > MAX_MATCH_COST:
        return False, f"Match cost too high (max {MAX_MATCH_COST})"

    return True, None


def validate_time_limit_ms(time_limit_ms: int) -> Tuple[bool, Optional[str]]:
    """Validate time limit in milliseconds.

    Args:
        time_limit_ms: Time limit in milliseconds.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(time_limit_ms, (int, float)):
        return False, "Time limit must be a number"

    if time_limit_ms < MIN_TIME_LIMIT_MS:
        return False, f"Time limit too short (min {MIN_TIME_LIMIT_MS}ms)"

    if time_limit_ms > MAX_TIME_LIMIT_MS:
        return False, f"Time limit too long (max {MAX_TIME_LIMIT_MS}ms)"

    return True, None


def validate_ranked_parameter(ranked: bool) -> Tuple[bool, Optional[str]]:
    """Validate ranked parameter.

    Args:
        ranked: The ranked boolean value.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(ranked, bool):
        return False, "Ranked must be a boolean"

    return True, None


def validate_limit_parameter(limit: int, max_limit: int = 500) -> Tuple[bool, Optional[str]]:
    """Validate limit parameter for pagination.

    Args:
        limit: The limit value.
        max_limit: Maximum allowed limit.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(limit, int):
        return False, "Limit must be an integer"

    if limit < 1:
        return False, "Limit must be at least 1"

    if limit > max_limit:
        return False, f"Limit too large (max {max_limit})"

    return True, None


def validate_response_data(response: Any, required_fields: list[str]) -> Tuple[bool, Optional[str]]:
    """Validate response data contains required fields.

    Args:
        response: The response data to validate.
        required_fields: List of required field names.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if response is None:
        return False, "Response data is None"

    if not isinstance(response, dict):
        return False, "Response must be a dictionary"

    missing_fields = [field for field in required_fields if field not in response]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    return True, None


def validate_health_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate health check response.

    Args:
        response: The health response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(response, dict):
        return False, "Health response must be a dictionary"

    # Health response should have 'status' field
    if "status" not in response:
        return False, "Health response missing 'status' field"

    status = response["status"]
    if status not in ["healthy", "unhealthy", "degraded"]:
        return False, f"Invalid health status: {status}"

    return True, None


def validate_agent_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate agent creation/listing response.

    Args:
        response: The agent response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    return validate_response_data(response, ["id", "name", "game_type"])


def validate_match_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate match response.

    Args:
        response: The match response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    return validate_response_data(response, ["match_id", "status", "game_type"])


def validate_queue_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate queue response.

    Args:
        response: The queue response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    return validate_response_data(response, ["status"])


def validate_rating_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate rating response.

    Args:
        response: The rating response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Rating response should have ranking info
    if not isinstance(response, dict):
        return False, "Rating response must be a dictionary"

    if "ranking" not in response:
        return False, "Rating response missing 'ranking' field"

    return True, None


def validate_wallet_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate wallet response.

    Args:
        response: The wallet response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    return validate_response_data(response, ["balance", "currency"])


def validate_transaction_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate transaction response.

    Args:
        response: The transaction response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    return validate_response_data(response, ["transactions", "total", "page"])


def validate_game_state_response(response: Any) -> Tuple[bool, Optional[str]]:
    """Validate game state response.

    Args:
        response: The game state response to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(response, dict):
        return False, "Game state response must be a dictionary"

    # Game state should have 'state' or equivalent
    state_keys = ["state", "observation", "board", "game_state"]
    has_state = any(key in response for key in state_keys)

    if not has_state:
        return False, "Game state response missing state data"

    return True, None


def validate_memory_report(memory_bytes: Any) -> Tuple[bool, Optional[str]]:
    """Validate memory report value.

    Args:
        memory_bytes: The memory value in bytes.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(memory_bytes, (int, float)):
        return False, "Memory bytes must be a number"

    if memory_bytes < 0:
        return False, "Memory bytes cannot be negative"

    # 10GB sanity check
    if memory_bytes > 10 * 1024 * 1024 * 1024:
        return False, "Memory value exceeds reasonable limit (10GB)"

    return True, None


def validate_ssl_config(verify_ssl: bool, base_url: str = "") -> Tuple[bool, Optional[str]]:
    """Validate SSL configuration.

    Security Note:
        SSL verification should always be enabled in production environments.
        Disabling SSL verification makes the connection vulnerable to MITM attacks.

    Args:
        verify_ssl: Whether to verify SSL certificates.
        base_url: Optional base URL to check if this is a production environment.

    Returns:
        Tuple of (is_valid, warning_message).
        Returns False if SSL is disabled in production.
    """
    if not isinstance(verify_ssl, bool):
        return False, "verify_ssl must be a boolean"

    # Check if this appears to be a production URL
    is_production = (
        base_url.startswith("https://") and 
        ("aitabletop.com" in base_url or "api.aitabletop" in base_url)
    )

    if not verify_ssl and is_production:
        return False, "SSL verification cannot be disabled for production URLs"

    if not verify_ssl:
        return True, "Warning: SSL verification disabled. Use only for local development!"

    return True, None


def validate_fallback_config(fallback_on_error: bool) -> Tuple[bool, Optional[str]]:
    """Validate fallback configuration.

    Args:
        fallback_on_error: Whether to use fallback on error.

    Returns:
        Tuple of (is_valid, warning_message).
    """
    if not isinstance(fallback_on_error, bool):
        return False, "fallback_on_error must be a boolean"

    return True, None


def validate_action_result(action_result: Any) -> Tuple[bool, Optional[str]]:
    """Validate action result from agent.act().

    Args:
        action_result: The result from agent.act().

    Returns:
        Tuple of (is_valid, error_message).
    """
    if action_result is None:
        return False, "Agent action returned None"

    if not isinstance(action_result, dict):
        return False, f"Agent action must return a dict, got {type(action_result).__name__}"

    return True, None


def validate_legal_moves(observation: dict, action: dict) -> Tuple[bool, Optional[str]]:
    """Validate that action is in legal moves.

    Args:
        observation: The game observation.
        action: The proposed action.

    Returns:
        Tuple of (is_valid, error_message).
    """
    legal_moves = observation.get("legal_moves") or observation.get("legal_actions", [])

    if not legal_moves:
        # No legal moves to validate against
        return True, None

    # Get the move from action
    move = action.get("move")
    if move is None:
        return False, "Action missing 'move' key"

    # Check if move is in legal moves
    if move not in legal_moves:
        return False, f"Move '{move}' is not in legal moves: {legal_moves[:5]}..."

    return True, None


class ValidationError(AITabletopError):
    """Raised when validation fails."""

    pass


class Validator:
    """Convenience class for chaining validations."""

    def __init__(self):
        """Initialize the validator."""
        self.errors: list[str] = []

    def validate(self, check: bool, message: str) -> "Validator":
        """Add an error if check fails.

        Args:
            check: The condition to check.
            message: Error message if check is False.

        Returns:
            Self for chaining.
        """
        if not check:
            self.errors.append(message)
        return self

    def is_valid(self) -> bool:
        """Check if all validations passed.

        Returns:
            True if no errors.
        """
        return len(self.errors) == 0

    def get_errors(self) -> list[str]:
        """Get list of all errors.

        Returns:
            List of error messages.
        """
        return self.errors

    def raise_if_invalid(self) -> None:
        """Raise ValidationError if any checks failed.

        Raises:
            ValidationError: If any validations failed.
        """
        if self.errors:
            error_msg = "; ".join(self.errors)
            raise ValidationError(f"Validation failed: {error_msg}")

    def clear(self) -> "Validator":
        """Clear all errors.

        Returns:
            Self for chaining.
        """
        self.errors = []
        return self