"""Heuristic chess agent using material counting."""

from __future__ import annotations

from typing import Any

from agentforge.agents.base import BaseAgent


class HeuristicChessAgent(BaseAgent):
    """A chess agent that uses simple material counting heuristic.

    This agent evaluates positions based on material advantage and selects
    moves that maximize the material count difference. It's a good baseline
    for chess that plays reasonably without requiring neural networks.

    Requires the `python-chess` package:
        pip install chess

    Example:
        import os
        agent = HeuristicChessAgent()
        client = RLArenaClient(api_key=os.environ.get("RL_ARENA_API_KEY"))
        result = client.play_match(match_id, agent)
    """

    # Standard piece values (pawn=1, knight/bishop=3, rook=5, queen=9)
    PIECE_VALUES: dict[str, int] = {
        "p": 1,  # Pawn
        "n": 3,  # Knight
        "b": 3,  # Bishop
        "r": 5,  # Rook
        "q": 9,  # Queen
        "k": 0,  # King (invaluable, but we assign 0 for counting)
    }

    def __init__(self, depth: int = 1) -> None:
        """Initialize the heuristic chess agent.

        Args:
            depth: Search depth for move evaluation (default: 1, greedy).
                   Higher depths are slow and not recommended for this simple agent.
        """
        self.depth = depth
        self._has_chess = False
        self._chess_module: Any = None

    def _ensure_chess(self) -> None:
        """Ensure chess module is available."""
        if not self._has_chess:
            try:
                import chess

                self._chess_module = chess
                self._has_chess = True
            except ImportError as e:
                raise ImportError(
                    "HeuristicChessAgent requires the 'chess' package. "
                    "Install it with: pip install chess"
                ) from e

    def act(self, observation: dict[str, Any], time_limit_ms: int) -> dict[str, Any]:
        """Select the best move using material counting heuristic.

        Args:
            observation: Chess observation dict with "fen" and "legal_moves".
            time_limit_ms: Time limit in milliseconds (mostly ignored).

        Returns:
            dict with "move" key containing the selected UCI move.
        """
        self._ensure_chess()

        fen = observation.get("fen")
        legal_moves = observation.get("legal_moves", [])

        if not fen or not legal_moves:
            raise ValueError("Observation missing 'fen' or 'legal_moves'")

        # Create chess board from FEN
        board = self._chess_module.Board(fen)

        # Evaluate each legal move
        best_move = None
        best_score = float("-inf")

        for uci_move in legal_moves:
            try:
                move = self._chess_module.Move.from_uci(uci_move)
                if move not in board.legal_moves:
                    continue

                # Make the move and evaluate
                board.push(move)
                score = self._evaluate_position(board)
                board.pop()

                if score > best_score:
                    best_score = score
                    best_move = uci_move

            except Exception:
                # Skip invalid moves
                continue

        if best_move is None:
            # Fallback to first legal move if evaluation fails
            best_move = legal_moves[0]

        return {"move": best_move}

    def _evaluate_position(self, board: Any) -> float:
        """Evaluate a position using material counting.

        Args:
            board: A python-chess Board object.

        Returns:
            Score from the perspective of the side to move.
            Positive = advantage for side to move.
        """
        score = 0.0

        for square in self._chess_module.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            # Get piece value
            piece_type = piece.symbol().lower()
            value = self.PIECE_VALUES.get(piece_type, 0)

            # Add for our pieces, subtract for opponent's pieces
            # Note: board.turn is the side to move, so we want positive for our pieces
            if piece.color == board.turn:
                score += value
            else:
                score -= value

        return score