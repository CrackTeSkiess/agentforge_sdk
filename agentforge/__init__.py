"""RL Arena Python SDK.

A client library for interacting with the RL Arena platform,
where RL agents compete in multiplayer games.

Example:
    import os
    from agentforge import RLArenaClient, BaseAgent, RandomAgent

    client = RLArenaClient(api_key=os.environ.get("RL_ARENA_API_KEY"))
    agent_info = client.register_agent("MyBot", "chess")
    print(f"Agent created: {agent_info['agent_id']}")

Security Notes:
    - Store API keys securely using environment variables
    - Never commit API keys to source control
    - Always use HTTPS in production
"""

__version__ = "0.1.0"

from agentforge.agents.base import BaseAgent
from agentforge.agents.heuristic_chess import HeuristicChessAgent
from agentforge.agents.random_agent import RandomAgent
from agentforge.client import RLArenaClient
from agentforge.exceptions import (
    AgentError,
    AgentSuspendedError,
    AuthenticationError,
    ConnectionError,
    InsufficientFundsError,
    InvalidActionError,
    MatchNotFoundError,
    MemoryLimitExceeded,
    RateLimitError,
    RLArenaError,
    TimeoutError,
    WrongTurnError,
)
from agentforge.memory_tracker import MemoryTracker
from agentforge.validators import (
    SUPPORTED_GAMES,
    Validator,
    ValidationError,
    validate_action,
    validate_action_result,
    validate_agent_id,
    validate_agent_name,
    validate_agent_response,
    validate_api_key,
    validate_base_url,
    validate_fallback_config,
    validate_game_state_response,
    validate_game_type,
    validate_health_response,
    validate_legal_moves,
    validate_limit_parameter,
    validate_match_cost,
    validate_match_id,
    validate_match_response,
    validate_memory_report,
    validate_observation,
    validate_queue_id,
    validate_queue_response,
    validate_ranked_parameter,
    validate_rating_response,
    validate_response_data,
    validate_retry_count,
    validate_ssl_config,
    validate_time_limit_ms,
    validate_transaction_response,
    validate_wallet_response,
)

__all__ = [
    # Main classes
    "RLArenaClient",
    "BaseAgent",
    "RandomAgent",
    "HeuristicChessAgent",
    # Memory tracking
    "MemoryTracker",
    # Validators
    "Validator",
    "ValidationError",
    "SUPPORTED_GAMES",
    # Version
    "__version__",
    # Validation functions
    "validate_api_key",
    "validate_game_type",
    "validate_agent_name",
    "validate_match_id",
    "validate_agent_id",
    "validate_queue_id",
    "validate_timeout",
    "validate_retry_count",
    "validate_action",
    "validate_action_result",
    "validate_observation",
    "validate_base_url",
    "validate_match_cost",
    "validate_time_limit_ms",
    "validate_ranked_parameter",
    "validate_limit_parameter",
    "validate_response_data",
    "validate_health_response",
    "validate_agent_response",
    "validate_match_response",
    "validate_queue_response",
    "validate_rating_response",
    "validate_wallet_response",
    "validate_transaction_response",
    "validate_game_state_response",
    "validate_memory_report",
    "validate_ssl_config",
    "validate_fallback_config",
    "validate_legal_moves",
    # Exceptions
    "RLArenaError",
    "AgentError",
    "TimeoutError",
    "InvalidActionError",
    "InsufficientFundsError",
    "AgentSuspendedError",
    "AuthenticationError",
    "MatchNotFoundError",
    "ConnectionError",
    "WrongTurnError",
    "RateLimitError",
    "MemoryLimitExceeded",
]