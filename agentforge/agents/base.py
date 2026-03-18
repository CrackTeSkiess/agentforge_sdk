"""Base agent abstract class for RL Arena."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from agentforge.memory_tracker import MemoryTracker


class BaseAgent(ABC):
    """Abstract base class for all RL Arena agents.

    All agents must inherit from this class and implement the `act` method.
    The act method is called each time it is the agent's turn to make a move.

    Example:
        class MyAgent(BaseAgent):
            def act(self, observation: dict, time_limit_ms: int) -> dict:
                # Your logic here
                return {"move": "e2e4"}
    """

    def __init__(self, memory_tracker: Optional[MemoryTracker] = None) -> None:
        """Initialize the base agent.

        Args:
            memory_tracker: Optional MemoryTracker instance for tracking
                memory usage during agent operations.
        """
        self._memory_tracker = memory_tracker

    @abstractmethod
    def act(self, observation: dict[str, Any], time_limit_ms: int) -> dict[str, Any]:
        """Called each time it is your turn.

        Args:
            observation: Game state dict (schema is game-specific).
                Common keys include:
                - "legal_moves" or "legal_actions": List of valid moves
                - "is_your_turn": Boolean indicating if it's your turn
                - Game-specific state (see game-schemas.md)
            time_limit_ms: Hard deadline in milliseconds. Default: 5000ms.
                Use 80% as your internal budget to stay safe.

        Returns:
            dict with "move" key. Format is game-specific.
            The move MUST appear in observation["legal_moves"] or
            observation["legal_actions"].

        Raises:
            TimeoutError: If act() takes longer than time_limit_ms.

        Note:
            Penalties for violations:
            - Illegal move: +1 penalty point (turn skipped)
            - Timeout (act() takes longer than time_limit_ms): +2 penalty points
            - 3 penalty points total: match forfeited
        """
        pass

    def _track_memory_before_act(self) -> None:
        """Update memory tracking before act() is called.

        This is called internally by the client before invoking act().
        """
        if self._memory_tracker is not None:
            self._memory_tracker.get_memory_bytes()

    def _track_memory_after_act(self) -> None:
        """Update memory tracking after act() completes.

        This is called internally by the client after act() returns.
        """
        if self._memory_tracker is not None:
            self._memory_tracker.get_memory_bytes()

    def get_memory_usage(self) -> int:
        """Get current memory usage of the agent.

        Returns:
            Current RSS memory usage in bytes if a memory tracker was
            provided during initialization, otherwise returns 0.
        """
        if self._memory_tracker is not None:
            return self._memory_tracker.get_memory_bytes()
        return 0

    def on_game_start(self, match_id: str, game_type: str, agent_ids: list[str]) -> None:
        """Called when a game starts.

        Args:
            match_id: The unique identifier for this match.
            game_type: The type of game being played (e.g., "chess", "uno").
            agent_ids: List of all agent IDs participating in this match.
        """
        pass

    def on_game_end(
        self,
        match_id: str,
        result: str,
        score: float,
        reason: Optional[str] = None,
    ) -> None:
        """Called when a game ends.

        Args:
            match_id: The unique identifier for this match.
            result: The result for this agent ("win", "loss", or "draw").
            score: Numeric score (1.0 for win, 0.0 for loss, 0.5 for draw).
            reason: Optional reason for game end (e.g., "checkmate", "timeout").
        """
        pass

    def on_error(self, error_code: str, error_message: str) -> None:
        """Called when an error occurs during gameplay.

        Args:
            error_code: The error code (e.g., "INVALID_ACTION", "TIMEOUT").
            error_message: Human-readable error message.
        """
        pass