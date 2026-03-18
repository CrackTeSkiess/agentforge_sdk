"""Custom exceptions for AITabletop SDK."""

from __future__ import annotations


class AITabletopError(Exception):
    """Base exception for all AITabletop errors."""

    pass


class TimeoutError(AITabletopError):
    """Raised when an action takes longer than the time limit."""

    pass


class InvalidActionError(AITabletopError):
    """Raised when an invalid action is submitted."""

    pass


class InsufficientFundsError(AITabletopError):
    """Raised when wallet balance is too low for a ranked match."""

    pass


class AgentSuspendedError(AITabletopError):
    """Raised when an agent has 3+ forfeits and cannot join queue."""

    pass


class AuthenticationError(AITabletopError):
    """Raised when API key is invalid or expired."""

    pass


class MatchNotFoundError(AITabletopError):
    """Raised when match_id does not exist or agent is not a participant."""

    pass


class ConnectionError(AITabletopError):
    """Raised when WebSocket connection fails."""

    pass


class WrongTurnError(AITabletopError):
    """Raised when an action is submitted when it's not the agent's turn."""

    pass


class RateLimitError(AITabletopError):
    """Raised when rate limit is exceeded."""

    pass


class AgentError(AITabletopError):
    """Raised when an agent fails to produce a valid action."""

    pass


class MemoryLimitExceeded(AITabletopError):
    """Raised when agent exceeds memory limit."""

    pass
