# AgentForge Python SDK

A Python SDK for building and deploying reinforcement learning agents on the RL Arena platform.

## Installation

```bash
pip install agentforge
```

For development with chess support:
```bash
pip install agentforge[chess,dev]
```

## Quick Start

```python
from agentforge import RLArenaClient, RandomAgent

# Initialize client
client = RLArenaClient(api_key="rla_live_your_key")

# Register an agent
agent_info = client.register_agent("MyBot", "chess")
print(f"Agent ID: {agent_info['agent_id']}")

# Join matchmaking queue
queue_info = client.join_queue(agent_info["agent_id"], "chess", ranked=True)
print(f"Queue ID: {queue_info['queue_id']}")

# Poll for match
import time
while True:
    status = client.get_queue_status(queue_info["queue_id"])
    if status["status"] == "matched":
        match_id = status["match_id"]
        break
    time.sleep(1)

# Play the match
agent = RandomAgent(seed=42)
result = client.play_match(match_id, agent)
print(f"Result: {result['result']}, New Rating: {result.get('new_rating')}")
```

## Creating a Custom Agent

```python
from agentforge import BaseAgent
import random

class MyAgent(BaseAgent):
    def act(self, observation, time_limit_ms):
        # Your logic here
        legal_moves = observation.get("legal_moves", [])
        return {"move": random.choice(legal_moves)}
```

## Features

- **RLArenaClient**: Full API client with HTTP and WebSocket support
- **BaseAgent**: Abstract base class for implementing agents
- **Built-in Agents**: RandomAgent, HeuristicChessAgent
- **Reconnection**: Automatic WebSocket reconnection with exponential backoff
- **Type Hints**: Full type annotations for Python 3.9+

## Supported Games

- Chess
- Go
- UNO
- Poker (Texas Hold'em)
- Tarot
- San Juan
- Qwixx

## License

MIT