"""RL Arena HTTP client for interacting with the platform API.

Security Notes:
    - API keys should be stored securely and never committed to source control
    - Use environment variables or secure secret management for API keys
    - Always use SSL/TLS (verify_ssl=True) in production
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
import time
import warnings
from typing import Any, Callable, Optional

import httpx
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

from agentforge.agents.base import BaseAgent
from agentforge.exceptions import (
    AgentError,
    AgentSuspendedError,
    AuthenticationError,
    ConnectionError as RLConnectionError,
    InsufficientFundsError,
    InvalidActionError,
    MatchNotFoundError,
    MemoryLimitExceeded,
    RateLimitError,
    RLArenaError,
    WrongTurnError,
)
from agentforge.validators import (
    SUPPORTED_GAMES,
    Validator,
    validate_action_result,
    validate_agent_id,
    validate_agent_name,
    validate_api_key,
    validate_base_url,
    validate_fallback_config,
    validate_game_type,
    validate_health_response,
    validate_limit_parameter,
    validate_match_id,
    validate_memory_report,
    validate_observation,
    validate_queue_id,
    validate_ranked_parameter,
    validate_response_data,
    validate_retry_count,
    validate_ssl_config,
    validate_timeout,
)

logger = logging.getLogger(__name__)

# SDK version for User-Agent header
SDK_VERSION = "0.1.0"
DEFAULT_USER_AGENT = f"agentforge-sdk/{SDK_VERSION}"
DEFAULT_TIMEOUT = 30.0


class RLArenaClient:
    """Client for the RL Arena platform API.

    This client provides methods to interact with the RL Arena platform,
    including agent registration, matchmaking, and gameplay via WebSocket.

    Security Notes:
        - API keys should be stored securely and never committed to source control
        - Use environment variables or secure secret management for API keys
        - Always use SSL/TLS (verify_ssl=True) in production
        - API keys are sent in headers but should be protected via HTTPS

    Example:
        import os
        client = RLArenaClient(api_key=os.environ.get("RL_ARENA_API_KEY"))
        agent_info = client.register_agent("MyBot", "chess")
        queue_info = client.join_queue(agent_info["agent_id"], "chess")
        # ... poll for match ...
        result = client.play_match(match_id, MyAgent())

    Attributes:
        base_url: Base URL for the API.
        timeout: HTTP request timeout in seconds.
        verify_ssl: Whether to verify SSL certificates.
        fallback_on_error: If True, use random move when agent fails.
        max_retries: Maximum number of retries for connections.
        retry_delay: Initial retry delay in seconds.
    """

    # Connection retry configuration
    DEFAULT_MAX_RETRIES = 5
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 30.0  # Cap exponential backoff at 30 seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.rlarena.com",
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
        fallback_on_error: bool = False,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ):
        """Initialize the RL Arena client.

        Security Notes:
            - API key should be provided via environment variable or secure secret management
            - Never hardcode API keys in source code
            - The API key is stored in memory only and never logged

        Args:
            api_key: Your API key (format: rla_live_xxxxxxxx or rla_test_xxxxxxxx).
                    If None, will attempt to read from RL_ARENA_API_KEY environment variable.
            base_url: Base URL for the API. Use "http://localhost:8000" for local dev.
                     Production URLs must use HTTPS.
            timeout: HTTP request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates. Default True.
                      WARNING: Setting to False is only for local development with self-signed certs.
                      In production, always use verify_ssl=True to prevent MITM attacks.
            fallback_on_error: If True, use random move when agent fails.
                              If False (default), raise exceptions on agent error.
            max_retries: Maximum number of WebSocket connection retries.
                        Defaults to DEFAULT_MAX_RETRIES (5).
            retry_delay: Initial retry delay in seconds.
                        Defaults to DEFAULT_RETRY_DELAY (1.0).

        Raises:
            AuthenticationError: If API key is invalid or missing.
            RLArenaError: If configuration is invalid or SSL is disabled in production.
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.environ.get("RL_ARENA_API_KEY")
            if api_key is None:
                raise AuthenticationError(
                    "API key not provided. Set RL_ARENA_API_KEY environment variable "
                    "or pass api_key parameter."
                )
        
        # Validate API key
        is_valid, error_msg = validate_api_key(api_key)
        if not is_valid:
            raise AuthenticationError(f"Invalid API key: {error_msg}")
        
        # Store API key securely (not logged, masked in repr)
        self._api_key = api_key

        # Validate base URL
        is_valid, error_msg = validate_base_url(base_url)
        if not is_valid:
            raise RLArenaError(f"Invalid base URL: {error_msg}")
        
        # Security check: warn if using HTTP in production
        is_production_url = base_url.startswith("https://") or "api.rlarena.com" in base_url
        if not base_url.startswith("https://") and is_production_url:
            logger.warning(
                "SECURITY WARNING: Using non-HTTPS connection for production URL. "
                "This may expose your API key to interception."
            )
        
        self.base_url = base_url.rstrip("/")

        # Validate timeout
        is_valid, error_msg = validate_timeout(timeout)
        if not is_valid:
            raise RLArenaError(f"Invalid timeout: {error_msg}")
        self.timeout = timeout

        # Validate SSL config - enforce SSL in production
        is_valid, error_msg = validate_ssl_config(verify_ssl, self.base_url)
        if not is_valid:
            raise RLArenaError(f"Invalid SSL config: {error_msg}")
        
        # Security check: warn if SSL verification is disabled
        if not verify_ssl:
            logger.warning(
                "SECURITY WARNING: SSL verification is disabled. "
                "This makes the connection vulnerable to MITM attacks. "
                "Only use for local development with self-signed certificates."
            )
        self.verify_ssl = verify_ssl

        # Validate fallback config
        is_valid, error_msg = validate_fallback_config(fallback_on_error)
        if not is_valid:
            raise RLArenaError(f"Invalid fallback config: {error_msg}")
        self.fallback_on_error = fallback_on_error

        # Validate and set retry configuration
        if max_retries is not None:
            is_valid, error_msg = validate_retry_count(max_retries)
            if not is_valid:
                raise RLArenaError(f"Invalid max_retries: {error_msg}")
        self.max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES

        self.retry_delay = retry_delay if retry_delay is not None else self.DEFAULT_RETRY_DELAY

        # Create SSL context for WebSocket connections
        if verify_ssl:
            self._ssl_context = ssl.create_default_context()
        else:
            # Disable SSL verification (development only)
            self._ssl_context = ssl._create_unverified_context()

        # Determine WS URL from HTTP URL
        if self.base_url.startswith("https://"):
            self.ws_base_url = self.base_url.replace("https://", "wss://")
        elif self.base_url.startswith("http://"):
            self.ws_base_url = self.base_url.replace("http://", "ws://")
        else:
            # Assume https for bare domains
            self.ws_base_url = f"wss://{self.base_url}"

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": DEFAULT_USER_AGENT,
            },
            timeout=timeout,
            verify=verify_ssl,
        )

        logger.info(f"RLArenaClient initialized with base_url={self.base_url}")

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error responses and raise appropriate exceptions.

        Args:
            response: The HTTP response to handle.

        Raises:
            AuthenticationError: For 401/403 responses.
            InsufficientFundsError: For 402 responses.
            MatchNotFoundError: For 404 responses related to matches.
            RateLimitError: For 429 responses.
            InvalidActionError: For invalid action responses.
            WrongTurnError: For turn-related errors.
            AgentSuspendedError: For 409 responses.
            RLArenaError: For other error responses.
        """
        if response.status_code == 200 or response.status_code == 201:
            return

        error_data: dict[str, Any] = {}
        try:
            error_data = response.json()
        except Exception:
            pass

        # Sanitize error detail to prevent information leakage
        error_detail = error_data.get("detail", "An error occurred")
        if len(error_detail) > 500:
            error_detail = error_detail[:497] + "..."

        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(f"Authentication failed: {error_detail}")
        elif response.status_code == 402:
            raise InsufficientFundsError(f"Insufficient funds: {error_detail}")
        elif response.status_code == 404:
            if "match" in error_detail.lower():
                raise MatchNotFoundError(f"Match not found: {error_detail}")
            raise RLArenaError(f"Resource not found: {error_detail}")
        elif response.status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {error_detail}")
        elif response.status_code == 400:
            if "illegal" in error_detail.lower() or "invalid" in error_detail.lower():
                raise InvalidActionError(f"Invalid action: {error_detail}")
            elif "turn" in error_detail.lower():
                raise WrongTurnError(f"Wrong turn: {error_detail}")
            raise RLArenaError(f"Bad request: {error_detail}")
        elif response.status_code == 409:
            raise AgentSuspendedError(f"Agent suspended: {error_detail}")
        else:
            response.raise_for_status()

    def register_agent(self, name: str, game_type: str) -> dict[str, Any]:
        """Register a new agent for a specific game.

        Args:
            name: Unique name within your account (max 100 chars).
            game_type: One of "chess", "go", "uno", "poker", "tarot", "san_juan", "qwixx".

        Returns:
            dict with agent_id, name, game_type, created_at.

        Raises:
            AuthenticationError: If API key is invalid.
            RLArenaError: If agent name already exists or game_type is invalid.
        """
        # Validate agent name
        is_valid, error_msg = validate_agent_name(name)
        if not is_valid:
            raise RLArenaError(f"Invalid agent name: {error_msg}")

        # Validate game type
        is_valid, error_msg = validate_game_type(game_type)
        if not is_valid:
            raise RLArenaError(f"Invalid game type: {error_msg}")

        response = self._client.post(
            "/api/v1/players/",
            json={"name": name, "game_type": game_type},
        )
        self._handle_error(response)

        data = response.json()

        # Validate response
        is_valid, error_msg = validate_response_data(data, ["id", "name", "game_type"])
        if not is_valid:
            logger.warning(f"Invalid response data: {error_msg}")

        return {
            "agent_id": data["id"],
            "name": data["name"],
            "game_type": data["game_type"],
            "created_at": data.get("created_at", ""),
        }

    def join_queue(
        self, agent_id: str, game_type: str, ranked: bool = True
    ) -> dict[str, Any]:
        """Enter the matchmaking queue.

        Args:
            agent_id: ID from register_agent().
            game_type: Must match agent's registered game type.
            ranked: True affects Glicko-2 rating and costs match fee;
                   False is cheaper practice.

        Returns:
            dict with queue_id, status, estimated_wait.

        Raises:
            InsufficientFundsError: If wallet balance is too low for ranked match.
            AuthenticationError: If API key is invalid.
            RLArenaError: If agent not found or game type mismatch.
        """
        # Validate agent_id
        is_valid, error_msg = validate_agent_id(agent_id)
        if not is_valid:
            raise RLArenaError(f"Invalid agent ID: {error_msg}")

        # Validate game type
        is_valid, error_msg = validate_game_type(game_type)
        if not is_valid:
            raise RLArenaError(f"Invalid game type: {error_msg}")

        # Validate ranked parameter
        is_valid, error_msg = validate_ranked_parameter(ranked)
        if not is_valid:
            raise RLArenaError(f"Invalid ranked parameter: {error_msg}")

        response = self._client.post(
            "/api/v1/queue/join",
            json={
                "agent_id": agent_id,
                "game_type": game_type,
                "ranked": ranked,
            },
        )
        self._handle_error(response)

        data = response.json()
        result: dict[str, Any] = {
            "queue_id": data.get("queue_id", ""),
            "status": data["status"],
        }

        # Parse estimated wait from message if present
        message = data.get("message", "")
        if "estimated" in message.lower():
            # Try to extract number from message
            import re

            match = re.search(r"(\d+)", message)
            if match:
                result["estimated_wait"] = int(match.group(1))
        else:
            result["estimated_wait"] = 30  # Default estimate

        return result

    def get_queue_status(self, queue_id: str) -> dict[str, Any]:
        """Poll for match assignment. Call every 1-2 seconds.

        Args:
            queue_id: Queue ID from join_queue().

        Returns:
            dict with status ("waiting" or "matched").
            If matched, includes match_id.
            If waiting, includes position and estimated_wait.

        Raises:
            RLArenaError: If queue ID is invalid.
        """
        # Validate queue_id
        is_valid, error_msg = validate_queue_id(queue_id)
        if not is_valid:
            raise RLArenaError(f"Invalid queue ID: {error_msg}")

        response = self._client.get(f"/api/v1/queue/status/{queue_id}")
        self._handle_error(response)

        data = response.json()
        result: dict[str, Any] = {"status": data["status"]}

        if data["status"] == "matched":
            result["match_id"] = data.get("match_id")
        else:
            result["position"] = data.get("position", 0)
            result["estimated_wait"] = data.get("estimated_wait_seconds", 30)

        return result

    def play_match(
        self,
        match_id: str,
        agent: BaseAgent,
        on_state: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> dict[str, Any]:
        """Connect via WebSocket and play the match using your agent.

        This method handles the full WebSocket loop: connects, receives
        your_turn messages, calls agent.act(), submits actions via HTTP POST,
        and receives game_over.

        Args:
            match_id: Match ID from get_queue_status().
            agent: Your agent instance (must inherit from BaseAgent).
            on_state: Optional callback called with state_dict before each
                     act() call - useful for logging.

        Returns:
            dict with game_over details including result, score, new_rating,
            rating_change, final_ratings.

        Raises:
            ConnectionError: If WebSocket connection fails after max retries.
            AuthenticationError: If API key is invalid.
            MatchNotFoundError: If match doesn't exist or agent not participant.
        """
        # Validate match_id
        is_valid, error_msg = validate_match_id(match_id)
        if not is_valid:
            raise RLArenaError(f"Invalid match ID: {error_msg}")

        # Validate agent is BaseAgent instance
        if not isinstance(agent, BaseAgent):
            raise RLArenaError("Agent must be an instance of BaseAgent")

        # Use asyncio to run the async implementation
        return asyncio.run(
            self._play_match_async(match_id, agent, on_state)
        )

    async def _play_match_async(
        self,
        match_id: str,
        agent: BaseAgent,
        on_state: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> dict[str, Any]:
        """Async implementation of play_match.

        Args:
            match_id: Match ID to play.
            agent: Agent instance to use.
            on_state: Optional state callback.

        Returns:
            Game result dictionary.
        """
        ws_url = f"{self.ws_base_url}/ws/play/{match_id}"
        headers = {"X-API-Key": self._api_key}

        max_retries = self.max_retries
        retry_delay = self.retry_delay

        game_result: Optional[dict[str, Any]] = None
        connected = False

        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to WebSocket (attempt {attempt + 1}/{max_retries})")
                logger.debug(f"WebSocket URL: {ws_url}")

                async with websockets.connect(
                    ws_url,
                    additional_headers=headers,
                    ssl=self._ssl_context,
                ) as websocket:
                    connected = True
                    logger.info("WebSocket connected")

                    # Notify agent game is starting
                    # We don't have full game info here, but agent can track state
                    agent.on_game_start(match_id, "", [])

                    # Main message loop
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type")

                            if msg_type == "ping":
                                # Respond with pong
                                await websocket.send(json.dumps({"type": "pong"}))

                            elif msg_type == "memory_report_request":
                                # Server is request memory usage report
                                memory_bytes = agent.get_memory_usage()
                                is_valid, error_msg = validate_memory_report(memory_bytes)
                                if not is_valid:
                                    logger.warning(f"Invalid memory report: {error_msg}")
                                    memory_bytes = 0
                                await websocket.send(
                                    json.dumps({
                                        "type": "memory_report",
                                        "memory_bytes": memory_bytes,
                                    })
                                )

                            elif msg_type == "your_turn":
                                # It's our turn - call agent.act()
                                state = data.get("state", {})
                                time_limit_ms = data.get("time_limit_ms", 5000)
                                turn_number = data.get("turn_number", 0)

                                # Validate observation
                                is_valid, error_msg = validate_observation(state)
                                if not is_valid:
                                    logger.warning(f"Invalid observation: {error_msg}")

                                # Call optional state callback
                                if on_state:
                                    try:
                                        on_state(state)
                                    except Exception as e:
                                        logger.warning(f"on_state callback error: {e}")

                                # Track memory before act()
                                agent._track_memory_before_act()

                                # Call agent.act() with timeout handling
                                start_time = time.time()
                                try:
                                    action = agent.act(state, time_limit_ms)
                                except Exception as e:
                                    if self.fallback_on_error:
                                        logger.warning(f"Agent error, using fallback: {e}")
                                        # Try to recover with a random legal move
                                        legal_moves = state.get("legal_moves") or state.get(
                                            "legal_actions", []
                                        )
                                        if legal_moves:
                                            import random

                                            action = {"move": random.choice(legal_moves)}
                                        else:
                                            raise InvalidActionError(
                                                f"Agent failed and no legal moves: {e}"
                                            ) from e
                                    else:
                                        logger.error(f"Agent error (fallback disabled): {e}")
                                        raise AgentError(f"Agent failed to act: {e}") from e

                                # Validate action result
                                is_valid, error_msg = validate_action_result(action)
                                if not is_valid:
                                    logger.error(f"Invalid action from agent: {error_msg}")
                                    raise AgentError(f"Invalid action: {error_msg}")

                                # Track memory after act()
                                agent._track_memory_after_act()

                                elapsed_ms = (time.time() - start_time) * 1000
                                if elapsed_ms > time_limit_ms:
                                    logger.warning(
                                        f"Agent took {elapsed_ms:.0f}ms, "
                                        f"exceeding limit of {time_limit_ms}ms"
                                    )

                                # Submit action via HTTP POST
                                self._submit_action(match_id, action, turn_number)

                            elif msg_type == "state_update":
                                # State update from another player's action
                                pass  # Handled by server, no action needed

                            elif msg_type == "game_over":
                                # Game ended
                                game_result = {
                                    "type": "game_over",
                                    "result": data.get("result"),
                                    "score": data.get("score"),
                                    "reason": data.get("reason"),
                                    "new_rating": data.get("new_rating"),
                                    "rating_change": data.get("rating_change"),
                                    "final_ratings": data.get("final_ratings", {}),
                                }

                                # Notify agent
                                agent.on_game_end(
                                    match_id,
                                    data.get("result", ""),
                                    data.get("score", 0.0),
                                    data.get("reason"),
                                )

                                return game_result

                            elif msg_type == "error":
                                # Server error
                                error_code = data.get("code", "UNKNOWN")
                                error_message = data.get("message", "Unknown error")
                                logger.error(f"Server error: {error_code} - {error_message}")
                                agent.on_error(error_code, error_message)

                                # Some errors are fatal
                                if error_code in ["AUTH_FAILED", "MATCH_NOT_FOUND"]:
                                    raise RLArenaError(f"{error_code}: {error_message}")
                                elif error_code == "MEMORY_LIMIT_EXCEEDED":
                                    raise MemoryLimitExceeded(error_message)

                            elif msg_type == "rate_limited":
                                logger.warning("Rate limited by servers")
                                await asyncio.sleep(1)

                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON from server: {e}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")

            except InvalidStatusCode as e:
                # Handle WebSocket HTTP errors
                if e.status_code == 4001:
                    raise AuthenticationError("X-API-Key header required") from e
                elif e.status_code == 4002:
                    raise AuthenticationError("Invalid API key") from e
                elif e.status_code == 4004:
                    raise MatchNotFoundError(
                        "Match not found or you are not a participant"
                    ) from e
                elif e.status_code == 4005:
                    raise RLConnectionError(
                        "Duplicate connection - agent already connected elsewhere"
                    ) from e
                elif e.status_code == 4006:
                    # Memory limit exceeded error code
                    raise MemoryLimitExceeded(
                        "Agent exceeded memory limit during gameplay"
                    ) from e
                else:
                    logger.error(f"WebSocket HTTP error {e.status_code}")

            except ConnectionClosed as e:
                logger.warning(f"WebSocket closed: {e}")

            except Exception as e:
                logger.error(f"WebSocket error: {e}")

            # Connection lost - attempt reconnection if game not over
            if game_result is None and attempt < max_retries - 1:
                logger.info(f"Reconnecting in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                # Cap at MAX_RETRY_DELAY
                if retry_delay > self.MAX_RETRY_DELAY:
                    retry_delay = self.MAX_RETRY_DELAY
            else:
                break

        if not connected:
            raise RLConnectionError(
                f"Failed to connect to WebSocket after {max_retries} attempts"
            )

        if game_result is None:
            raise RLConnectionError(
                "Connection lost and game result not received"
            )

        return game_result

    def _submit_action(
        self, match_id: str, action: dict[str, Any], turn_number: Optional[int] = None
    ) -> None:
        """Submit an action via HTTP POST.

        Args:
            match_id: The match ID.
            action: The action dict (e.g., {"move": "e2e4"}).
            turn_number: Optional turn number for validation.
        """
        payload: dict[str, Any] = {"action": action}
        if turn_number is not None:
            payload["turn_number"] = turn_number

        response = self._client.post(
            f"/api/v1/matches/{match_id}/action",
            json=payload,
        )
        self._handle_error(response)
        # Log action type only, not full content (may contain sensitive data)
        action_summary = action.get("move", "unknown") if isinstance(action, dict) else "unknown"
        if len(str(action_summary)) > 50:
            action_summary = str(action_summary)[:47] + "..."
        logger.debug(f"Action submitted: type={action_summary}")

    def get_agent_stats(self, agent_id: str) -> dict[str, Any]:
        """Get agent statistics including rating and win/loss record.

        Args:
            agent_id: The agent ID.

        Returns:
            dict with agent_id, rating, rating_deviation, volatility,
            games_played, wins, losses, draws, win_rate.

        Raises:
            RLArenaError: If agent ID is invalid.
        """
        # Validate agent_id
        is_valid, error_msg = validate_agent_id(agent_id)
        if not is_valid:
            raise RLArenaError(f"Invalid agent ID: {error_msg}")

        response = self._client.get(f"/api/v1/players/{agent_id}")
        self._handle_error(response)

        data = response.json()
        ranking = data.get("ranking", {})

        games_played = ranking.get("games_played", 0)
        wins = ranking.get("wins", 0)
        losses = ranking.get("losses", 0)
        draws = ranking.get("draws", 0)

        win_rate = wins / games_played if games_played > 0 else 0.0

        result: dict[str, Any] = {
            "agent_id": agent_id,
            "rating": ranking.get("rating", 1500.0),
            "rating_deviation": ranking.get("rating_deviation", 350.0),
            "volatility": ranking.get("volatility", 0.06),
            "games_played": games_played,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": round(win_rate, 3),
        }

        return result

    def get_rating_history(self, agent_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get chronological rating history for an agent.

        Args:
            agent_id: The agent ID.
            limit: Maximum number of records (default: 100, max: 500).

        Returns:
            List of dicts with rating, rating_deviation, timestamp.

        Raises:
            RLArenaError: If agent ID is invalid or limit is out of range.
        """
        # Validate agent_id
        is_valid, error_msg = validate_agent_id(agent_id)
        if not is_valid:
            raise RLArenaError(f"Invalid agent ID: {error_msg}")

        # Validate limit
        is_valid, error_msg = validate_limit_parameter(limit, max_limit=500)
        if not is_valid:
            raise RLArenaError(f"Invalid limit: {error_msg}")

        response = self._client.get(
            f"/api/v1/players/{agent_id}/rating-history",
            params={"limit": limit},
        )
        self._handle_error(response)

        data = response.json()
        history = data.get("history", [])

        # Transform to consistent format
        result = []
        for entry in history:
            result.append({
                "rating": entry.get("rating", 1500.0),
                "rating_deviation": entry.get("rating_deviation", 350.0),
                "timestamp": entry.get("recorded_at", ""),
            })

        return result

    def get_match_replay(self, match_id: str) -> dict[str, Any]:
        """Get full game log for analysis.

        Args:
            match_id: The match ID.

        Returns:
            dict with match_id, game_type, result, states, actions.

        Raises:
            RLArenaError: If match ID is invalid.
        """
        # Validate match_id
        is_valid, error_msg = validate_match_id(match_id)
        if not is_valid:
            raise RLArenaError(f"Invalid match ID: {error_msg}")

        response = self._client.get(f"/api/v1/matches/{match_id}/replay")
        self._handle_error(response)

        data = response.json()

        # Transform states and actions to consistent format
        states = [
            {
                "turn_number": s.get("turn_number", 0),
                "agent_id": s.get("agent_id"),
                "state": s.get("state_data", {}),
            }
            for s in data.get("states", [])
        ]

        actions = [
            {
                "turn_number": a.get("turn_number", 0),
                "agent_id": a.get("agent_id"),
                "action": a.get("action_data", {}),
                "validated": a.get("validated", True),
                "error_message": a.get("error_message"),
            }
            for a in data.get("actions", [])
        ]

        result: dict[str, Any] = {
            "match_id": data.get("match_id", match_id),
            "game_type": data.get("game_type", ""),
            "status": data.get("status", ""),
            "states": states,
            "actions": actions,
        }

        # Add result info if available
        result_info = data.get("result")
        if result_info:
            result["result"] = result_info

        return result

    def list_games(self) -> list[dict[str, Any]]:
        """List all supported games with their costs.

        Returns:
            List of game info dicts with game_type, name, cost, etc.
        """
        response = self._client.get("/api/v1/games/")
        self._handle_error(response)
        games = response.json()

        # Validate games response
        if isinstance(games, list):
            for game in games:
                if "game_type" not in game:
                    logger.warning("Game missing game_type field")
        else:
            logger.warning("Games response is not a list")

        return games if isinstance(games, list) else []

    def health(self) -> dict[str, Any]:
        """Check API health status.

        Returns:
            dict with health status information.

        Raises:
            RLArenaError: If health check fails.
        """
        response = self._client.get("/health")
        response.raise_for_status()
        data = response.json()

        # Validate health response
        is_valid, error_msg = validate_health_response(data)
        if not is_valid:
            logger.warning(f"Health response validation warning: {error_msg}")

        return data

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._client.close()
        # Explicitly clear SSL context to release resources
        self._ssl_context = None

    def __enter__(self) -> RLArenaClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()