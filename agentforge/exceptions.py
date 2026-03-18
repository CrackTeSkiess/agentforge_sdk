"""Custom exceptions for RL Arena SDK."""

from __future__ import annotations


class RLArenaError(Exception):
    """Base exception for all RL Arena errors."""

    pass


class TimeoutError(RLArenaError):
    """Raised when an action takes longer than the time limit."""

    pass


class InvalidActionError(RLArenaError):
    """Raised when an invalid action is submitted."""

    pass


class InsufficientFundsError(RLArenaError):
    """Raised when wallet balance is too low for a ranked match."""

    pass


class AgentSuspendedError(RLArenaError):
    """Raised when an agent has 3+ forfeits and cannot join queue."""

    pass


class AuthenticationError(RLArenaError):
    """Raised when API key is invalid or expired."""

    pass


class MatchNotFoundError(RLArenaError):
    """Raised when match_id does not exist or agent is not a participant."""

    pass


class ConnectionError(RLArenaError):
    """Raised when WebSocket connection fails."""

    pass


class WrongTurnError(RLArenaError):
    """Raised when an action is submitted when it's not the agent's turn."""

    pass


class RateLimitError(RLArenaError):
    """Raised when rate limit is exceeded."""

    pass


class AgentError(RLArenaError):
    """Raised when an agent fails to produce a valid action."""

    pass


class MemoryLimitExceeded(RLArenaError):
    """Raised when agent exceeds memory limit."""

    pass