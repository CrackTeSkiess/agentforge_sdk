"""Tests for agentforge validators module."""
import pytest
from agentforge.validators import (
    validate_api_key,
    validate_game_type,
    validate_agent_name,
    validate_match_id,
    validate_timeout,
    validate_retry_count,
    validate_ranked_parameter,
    validate_limit_parameter,
    validate_health_response,
    ValidationError,
    Validator,
)


class TestValidateApiKey:
    """Tests for validate_api_key function."""

    def test_valid_api_key(self):
        """Test with a valid API key format."""
        is_valid, error = validate_api_key("rla_live_1234567890abcdef")
        assert is_valid is True
        assert error is None

    def test_empty_api_key(self):
        """Test with empty API key."""
        is_valid, error = validate_api_key("")
        assert is_valid is False
        assert error is not None

    def test_none_api_key(self):
        """Test with None API key."""
        is_valid, error = validate_api_key(None)
        assert is_valid is False
        assert error is not None


class TestValidateGameType:
    """Tests for validate_game_type function."""

    def test_valid_game_type(self):
        """Test with valid game type."""
        is_valid, error = validate_game_type("chess")
        assert is_valid is True
        assert error is None

    def test_empty_game_type(self):
        """Test with empty game type."""
        is_valid, error = validate_game_type("")
        assert is_valid is False
        assert error is not None


class TestValidateAgentName:
    """Tests for validate_agent_name function."""

    def test_valid_agent_name(self):
        """Test with valid agent name."""
        is_valid, error = validate_agent_name("MyAgent")
        assert is_valid is True
        assert error is None

    def test_empty_agent_name(self):
        """Test with empty agent name."""
        is_valid, error = validate_agent_name("")
        assert is_valid is False
        assert error is not None


class TestValidateTimeout:
    """Tests for validate_timeout function."""

    def test_valid_timeout(self):
        """Test with valid timeout."""
        is_valid, error = validate_timeout(30.0)
        assert is_valid is True
        assert error is None

    def test_negative_timeout(self):
        """Test with negative timeout."""
        is_valid, error = validate_timeout(-1.0)
        assert is_valid is False
        assert error is not None


class TestValidateRetryCount:
    """Tests for validate_retry_count function."""

    def test_valid_retry_count(self):
        """Test with valid retry count."""
        is_valid, error = validate_retry_count(3)
        assert is_valid is True
        assert error is None

    def test_negative_retry_count(self):
        """Test with negative retry count."""
        is_valid, error = validate_retry_count(-1)
        assert is_valid is False
        assert error is not None


class TestValidateRankedParameter:
    """Tests for validate_ranked_parameter function."""

    def test_ranked_true(self):
        """Test with ranked=True."""
        is_valid, error = validate_ranked_parameter(True)
        assert is_valid is True
        assert error is None

    def test_ranked_false(self):
        """Test with ranked=False."""
        is_valid, error = validate_ranked_parameter(False)
        assert is_valid is True
        assert error is None


class TestValidateLimitParameter:
    """Tests for validate_limit_parameter function."""

    def test_valid_limit(self):
        """Test with valid limit."""
        is_valid, error = validate_limit_parameter(100)
        assert is_valid is True
        assert error is None

    def test_zero_limit(self):
        """Test with zero limit."""
        is_valid, error = validate_limit_parameter(0)
        assert is_valid is False
        assert error is not None


class TestValidator:
    """Tests for Validator class."""

    def test_validator_initialization(self):
        """Test Validator initializes correctly."""
        validator = Validator()
        assert validator.is_valid() is True
        assert len(validator.get_errors()) == 0

    def test_validator_add_error(self):
        """Test Validator adds errors correctly."""
        validator = Validator()
        result = validator.validate(False, "Test error")
        assert isinstance(result, Validator)
        assert validator.is_valid() is False

    def test_validator_clear(self):
        """Test Validator clear method."""
        validator = Validator()
        validator.validate(False, "Test error")
        validator.clear()
        assert validator.is_valid() is True
        assert len(validator.get_errors()) == 0

    def test_validator_raise_if_invalid(self):
        """Test Validator raise_if_invalid method."""
        validator = Validator()
        validator.validate(False, "Test error")
        with pytest.raises(ValidationError):
            validator.raise_if_invalid()