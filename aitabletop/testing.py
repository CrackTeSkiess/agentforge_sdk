"""AITabletop Testing Suite.

This module provides testing utilities for AITabletop agents:
- Local game simulation
- Agent performance testing
- Match replay generation
- Statistical analysis
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

from aitabletop.agents.base import BaseAgent


@dataclass
class TestResult:
    """Result of a single test match."""
    match_id: str
    agent_id: str
    opponent: str
    result: str  # "win", "loss", "draw"
    score: float
    moves_made: int
    time_used_ms: int
    avg_response_time_ms: float
    legal_moves_made: int
    illegal_moves_made: int


@dataclass
class TestReport:
    """Report from running multiple tests."""
    agent_name: str
    game_type: str
    total_matches: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_score: float
    avg_moves: int
    avg_response_time_ms: float
    total_legal_moves: int
    total_illegal_moves: int
    legality_rate: float
    timestamp: str
    results: List[TestResult] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "game_type": self.game_type,
            "total_matches": self.total_matches,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_rate": round(self.win_rate, 3),
            "avg_score": round(self.avg_score, 2),
            "avg_moves": self.avg_moves,
            "avg_response_time_ms": round(self.avg_response_time_ms, 1),
            "total_legal_moves": self.total_legal_moves,
            "total_illegal_moves": self.total_illegal_moves,
            "legality_rate": round(self.legality_rate, 3),
            "timestamp": self.timestamp,
        }


class GameSimulator:
    """Simulates games for testing agents locally."""
    
    def __init__(self, game_type: str = "chess"):
        self.game_type = game_type
        self._game = None
    
    def create_game(self, agent_ids: List[str], config: Optional[Dict] = None) -> Any:
        """Create a new game instance."""
        # Import game dynamically
        if self.game_type == "chess":
            from app.games.chess_game import ChessGame
            self._game = ChessGame(agent_ids, config or {})
        elif self.game_type == "uno":
            from app.games.uno_game import UNOGame
            self._game = UNOGame(agent_ids, config or {})
        elif self.game_type == "poker":
            from app.games.poker_game import PokerGame
            self._game = PokerGame(agent_ids, config or {})
        else:
            raise ValueError(f"Unsupported game type: {self.game_type}")
        
        return self._game
    
    def get_state(self, agent_id: str) -> Dict:
        """Get current game state for an agent."""
        if self._game:
            return self._game.get_state(agent_id)
        return {}
    
    def validate_action(self, agent_id: str, action: Dict) -> bool:
        """Validate an action."""
        if self._game:
            valid, _ = self._game.validate_action(agent_id, action)
            return valid
        return False
    
    def apply_action(self, agent_id: str, action: Dict) -> None:
        """Apply an action to the game."""
        if self._game:
            self._game.apply_action(agent_id, action)
    
    def check_terminal(self) -> Optional[str]:
        """Check if game has ended."""
        if self._game:
            result = self._game.check_terminal()
            if result:
                return result.winner
        return None


class AgentTester:
    """Test suite for AITabletop agents."""
    
    def __init__(self, agent: BaseAgent, game_type: str = "chess"):
        self.agent = agent
        self.game_type = game_type
        self.simulator = GameSimulator(game_type)
        self._results: List[TestResult] = []
    
    async def run_tests(
        self,
        num_matches: int = 10,
        opponent: Optional[BaseAgent] = None,
        time_limit_ms: int = 5000,
    ) -> TestReport:
        """
        Run multiple test matches.
        
        Args:
            num_matches: Number of matches to play
            opponent: Opponent agent (uses random agent if None)
            time_limit_ms: Time limit per move
            
        Returns:
            TestReport with statistics
        """
        self._results = []
        
        for i in range(num_matches):
            result = await self._run_single_match(
                opponent=opponent,
                time_limit_ms=time_limit_ms,
            )
            self._results.append(result)
        
        return self._generate_report()
    
    async def _run_single_match(
        self,
        opponent: Optional[BaseAgent] = None,
        time_limit_ms: int = 5000,
    ) -> TestResult:
        """Run a single test match."""
        # Use random agent as opponent if none provided
        if opponent is None:
            from aitabletop.agents.random_agent import RandomAgent
            opponent = RandomAgent()
        
        # Create game
        agent_ids = ["test_agent", "opponent"]
        self.simulator = GameSimulator(self.game_type)
        self.simulator.create_game(agent_ids)
        
        # Game loop
        moves_made = 0
        legal_moves = 0
        illegal_moves = 0
        response_times = []
        current_turn = 0
        max_turns = 1000  # Prevent infinite loops
        
        while current_turn < max_turns:
            current_agent = self.agent if current_turn % 2 == 0 else opponent
            agent_id = "test_agent" if current_turn % 2 == 0 else "opponent"
            
            # Get state
            state = self.simulator.get_state(agent_id)
            
            # Time the response
            start = time.time()
            try:
                action = current_agent.act(state, time_limit_ms)
                response_time = (time.time() - start) * 1000
                response_times.append(response_time)
                
                # Validate
                if self.simulator.validate_action(agent_id, action):
                    self.simulator.apply_action(agent_id, action)
                    legal_moves += 1
                else:
                    illegal_moves += 1
                    # Try random legal move as fallback
                    if "legal_moves" in state and state["legal_moves"]:
                        fallback = random.choice(state["legal_moves"])
                        self.simulator.apply_action(agent_id, {"move": fallback})
                
            except Exception as e:
                illegal_moves += 1
            
            moves_made += 1
            current_turn += 1
            
            # Check if game ends
            winner = self.simulator.check_terminal()
            if winner:
                break
        
        # Determine result
        is_agent_turn = current_turn % 2 == 0
        if winner == "test_agent":
            result = "win"
            score = 1.0
        elif winner == "opponent":
            result = "loss"
            score = 0.0
        else:
            result = "draw"
            score = 0.5
        
        return TestResult(
            match_id=f"test_{datetime.now().timestamp()}",
            agent_id="test_agent",
            opponent="random" if opponent is None else "custom",
            result=result,
            score=score,
            moves_made=moves_made,
            time_used_ms=sum(response_times),
            avg_response_time_ms=sum(response_times) / len(response_times) if response_times else 0,
            legal_moves_made=legal_moves,
            illegal_moves_made=illegal_moves,
        )
    
    def _generate_report(self) -> TestReport:
        """Generate test report from results."""
        if not self._results:
            return TestReport(
                agent_name=self.agent.__class__.__name__,
                game_type=self.game_type,
                total_matches=0,
                wins=0,
                losses=0,
                draws=0,
                win_rate=0,
                avg_score=0,
                avg_moves=0,
                avg_response_time_ms=0,
                total_legal_moves=0,
                total_illegal_moves=0,
                legality_rate=0,
                timestamp=datetime.now().isoformat(),
            )
        
        wins = sum(1 for r in self._results if r.result == "win")
        losses = sum(1 for r in self._results if r.result == "loss")
        draws = sum(1 for r in self._results if r.result == "draw")
        total = len(self._results)
        
        return TestReport(
            agent_name=self.agent.__class__.__name__,
            game_type=self.game_type,
            total_matches=total,
            wins=wins,
            losses=losses,
            draws=draws,
            win_rate=wins / total if total > 0 else 0,
            avg_score=sum(r.score for r in self._results) / total,
            avg_moves=sum(r.moves_made for r in self._results) / total,
            avg_response_time_ms=sum(r.avg_response_time_ms for r in self._results) / total,
            total_legal_moves=sum(r.legal_moves_made for r in self._results),
            total_illegal_moves=sum(r.illegal_moves_made for r in self._results),
            legality_rate=sum(r.legal_moves_made for r in self._results) / 
                         (sum(r.legal_moves_made for r in self._results) + 
                          sum(r.illegal_moves_made for r in self._results)) if total > 0 else 0,
            timestamp=datetime.now().isoformat(),
            results=self._results,
        )


def test_agent_locally(
    agent: BaseAgent,
    game_type: str = "chess",
    num_matches: int = 10,
    time_limit_ms: int = 5000,
) -> Dict:
    """
    Quick test an agent locally.
    
    Args:
        agent: Agent to test
        game_type: Game type to test on
        num_matches: Number of matches
        time_limit_ms: Time limit per move
        
    Returns:
        Test results as dictionary
    """
    tester = AgentTester(agent, game_type)
    report = asyncio.run(tester.run_tests(num_matches, time_limit_ms=time_limit_ms))
    return report.to_dict()