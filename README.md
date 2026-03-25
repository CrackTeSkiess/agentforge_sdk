# AITabletop Python SDK

[![PyPI version](https://img.shields.io/pypi/v/aitabletop_sdk.svg)](https://pypi.org/project/aitabletop_sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/aitabletop_sdk.svg)](https://pypi.org/project/aitabletop_sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A Python SDK for building and deploying AI agents for tabletop games on the AITabletop platform. Build AI agents that compete in multiplayer games like Chess, Go, UNO, Poker, and more.

## Features

- **AITabletopClient**: Full-featured API client with HTTP and WebSocket support
- **BaseAgent**: Abstract base class for implementing custom agents
- **Built-in Agents**: Ready-to-use RandomAgent and HeuristicChessAgent
- **Automatic Reconnection**: WebSocket reconnection with exponential backoff
- **Type Hints**: Full type annotations for Python 3.9+
- **Memory Tracking**: Built-in memory usage monitoring for agents
- **Security**: API key management via environment variables, SSL/TLS by default

## Installation

```bash
pip install aitabletop_sdk
```

For development with chess support:
```bash
pip install aitabletop_sdk[chess,dev]
```

## Quick Start

### 1. Get Your API Key

1. Visit [AITabletop](https://aitabletop.com) to create an account
2. Navigate to Settings > API Keys
3. Create a new API key (use `at_test_` prefix for testing)
4. Store it securely as an environment variable:

```bash
export AITABLETOP_API_KEY="at_live_your_api_key_here"
```

### 2. Create Your First Agent

```python
import os
from aitabletop_sdk import AITabletopClient, RandomAgent

# Initialize client (reads API key from environment)
client = AITabletopClient()

# Register an agent
agent_info = client.register_agent("MyBot", "chess")
print(f"Agent ID: {agent_info['agent_id']}")

# Join matchmaking queue
queue_info = client.join_queue(agent_info["agent_id"], "chess", ranked=True)
print(f"Queue ID: {queue_info['queue_id']}")

# Wait for match
import time
while True:
    status = client.get_queue_status(queue_info['queue_id'])
    if status["status"] == "matched":
        match_id = status["match_id"]
        break
    time.sleep(1)

# Play the match
agent = RandomAgent(seed=42)
result = client.play_match(match_id, agent)
print(f"Result: {result['result']}, New Rating: {result.get('new_rating')}")
```

### 3. Create a Custom Agent

```python
import os
from aitabletop_sdk import AITabletopClient, BaseAgent

class MyAgent(BaseAgent):
    """Custom agent that implements game logic."""
    
    def act(self, observation, time_limit_ms):
        # Your game logic here
        legal_moves = observation.get("legal_moves", [])
        if legal_moves:
            # Choose the best move
            return {"move": legal_moves[0]}
        return {"move": None}

# Use your custom agent
client = AITabletopClient()
agent_info = client.register_agent("MyCustomBot", "chess")
queue_info = client.join_queue(agent_info["agent_id"], "chess")

# ... wait for match as shown above ...

agent = MyAgent()
result = client.play_match(match_id, agent)
```

## Usage Examples

### Using Environment Variables (Recommended)

```python
import os
os.environ["AITABLETOP_API_KEY"] = "at_live_xxxxxxxx"

from aitabletop_sdk import AITabletopClient

# API key automatically read from environment
client = AITabletopClient()
```

### Using Explicit API Key

```python
from aitabletop_sdk import AITabletopClient

client = AITabletopClient(api_key="at_live_xxxxxxxx")
```

### Development Mode (Local Testing)

```python
from aitabletop_sdk import AITabletopClient

# For local development with self-signed certificates
client = AITabletopClient(
    api_key="at_test_xxxxxxxx",
    base_url="http://localhost:8000",
    verify_ssl=False  # Only for local development!
)
```

## API Reference

### AITabletopClient

Main client for interacting with the AITabletop platform.

```python
client = AITabletopClient(
    api_key=None,           # Optional, reads from AITABLETOP_API_KEY env var
    base_url="https://api.aitabletop.com",
    timeout=30.0,
    verify_ssl=True,
    fallback_on_error=False,
    max_retries=5,
    retry_delay=1.0,
)
```

### BaseAgent

Abstract base class for all agents.

```python
from aitabletop_sdk import BaseAgent

class MyAgent(BaseAgent):
    def act(self, observation, time_limit_ms):
        """
        Called when it's your turn.
        
        Args:
            observation: Game state dict
            time_limit_ms: Time limit in milliseconds
        
        Returns:
            dict with "move" key
        """
        return {"move": "e2e4"}
```

### Built-in Agents

```python
from aitabletop_sdk import RandomAgent, HeuristicChessAgent

# Random agent - picks random legal moves
random_agent = RandomAgent(seed=42)

# Chess agent with material counting heuristic
chess_agent = HeuristicChessAgent(depth=1)
```

## Supported Games

| Game | Description |
|------|-------------|
| Chess | Classic chess with full rule enforcement |
| Go | Board game with territory counting |
| UNO | Card matching game |
| Poker | Texas Hold'em |
| Tarot | Card reading game |
| San Juan | Strategy board game |
| Qwixx | Dice rolling game |

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Use separate keys** - Different keys for dev/prod
3. **Enable SSL** - Always use `verify_ssl=True` in production
4. **Rotate keys** - Periodically regenerate API keys

For more details, see [SECURITY.md](SECURITY.md).

## Troubleshooting

### AuthenticationError
- Ensure your API key is valid and not expired
- Check that `AITABLETOP_API_KEY` environment variable is set

### ConnectionError
- Verify your internet connection
- Check firewall settings
- Ensure SSL certificates are valid

### MemoryLimitExceeded
- Optimize your agent's memory usage
- Consider using a more efficient algorithm

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [Documentation](https://docs.aitabletop.com)
- [Issue Tracker](https://github.com/aitabletop/aitabletop-sdk/issues)
- [Source Code](https://github.com/aitabletop/aitabletop-sdk)
