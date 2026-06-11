"""Tests for AITabletop SDK agents."""
import pytest

from aitabletop_sdk.agents.base import BaseAgent
from aitabletop_sdk.agents.random_agent import RandomAgent

SAMPLE_STATE = {
    "is_your_turn": True,
    "legal_moves": ["e2e4", "d2d4", "g1f3", "b1c3"],
}


class TestRandomAgent:
    """Tests for RandomAgent action selection."""

    def test_is_base_agent_subclass(self):
        """Test that RandomAgent inherits from BaseAgent."""
        agent = RandomAgent()
        assert isinstance(agent, BaseAgent)

    def test_act_returns_legal_move(self):
        """Test that act() returns a move from the legal moves list."""
        agent = RandomAgent()
        action = agent.act(SAMPLE_STATE, time_limit_ms=5000)
        assert isinstance(action, dict)
        assert action["move"] in SAMPLE_STATE["legal_moves"]

    def test_act_uses_legal_actions_key(self):
        """Test that act() falls back to the legal_actions key."""
        state = {"is_your_turn": True, "legal_actions": ["draw", "play_card"]}
        agent = RandomAgent()
        action = agent.act(state, time_limit_ms=5000)
        assert action["move"] in state["legal_actions"]

    def test_act_with_seed_is_reproducible(self):
        """Test that the same seed produces the same sequence of moves."""
        agent_a = RandomAgent(seed=42)
        agent_b = RandomAgent(seed=42)
        moves_a = [agent_a.act(SAMPLE_STATE, 5000)["move"] for _ in range(10)]
        moves_b = [agent_b.act(SAMPLE_STATE, 5000)["move"] for _ in range(10)]
        assert moves_a == moves_b

    def test_act_single_legal_move(self):
        """Test that the only legal move is always selected."""
        state = {"is_your_turn": True, "legal_moves": ["e2e4"]}
        agent = RandomAgent()
        action = agent.act(state, time_limit_ms=5000)
        assert action == {"move": "e2e4"}

    def test_act_no_legal_moves_raises(self):
        """Test that act() raises ValueError when no legal moves exist."""
        agent = RandomAgent()
        with pytest.raises(ValueError):
            agent.act({"is_your_turn": True, "legal_moves": []}, 5000)

    def test_act_missing_legal_moves_key_raises(self):
        """Test that act() raises ValueError when legal move keys are absent."""
        agent = RandomAgent()
        with pytest.raises(ValueError):
            agent.act({"is_your_turn": True}, 5000)
