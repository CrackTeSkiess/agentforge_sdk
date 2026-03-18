"""Random agent that picks random legal moves."""

from __future__ import annotations

import random
from typing import Any

from agentforge.agents.base import BaseAgent


class RandomAgent(BaseAgent):
    """An agent that selects random legal moves.

    This is a simple baseline agent that randomly selects from available
    legal moves. It's useful for testing and as a baseline for comparison.

    Example:
        import os
        agent = RandomAgent(seed=42)  # Optional seed for reproducibility
        client = RLArenaClient(api_key=os.environ.get("RL_ARENA_API_KEY"))
        result = client.play_match(match_id, agent)
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize the random agent.

        Args:
            seed: Optional random seed for reproducible behavior.
        """
        self.rng = random.Random(seed)

    def act(self, observation: dict[str, Any], time_limit_ms: int) -> dict[str, Any]:
        """Select a random legal move.

        Args:
            observation: Game state dict containing legal moves.
            time_limit_ms: Time limit in milliseconds (ignored by this agent).

        Returns:
            dict with "move" key containing the selected move.

        Raises:
            ValueError: If no legal moves are available.
        """
        # Get legal moves from observation (different games use different keys)
        legal_moves = observation.get("legal_moves") or observation.get("legal_actions")

        if not legal_moves:
            raise ValueError("No legal moves available in observation")

        # Select a random move
        move = self.rng.choice(legal_moves)

        return {"move": move}