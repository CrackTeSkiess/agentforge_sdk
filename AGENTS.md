# AITabletop SDK - Agent Guide

This document provides essential information for AI coding agents working on the AITabletop Python SDK project.

## Project Overview

**AITabletop Python SDK** is a client library for building and deploying AI agents for tabletop games on the AITabletop platform. The SDK enables developers to create AI agents that compete in multiplayer games like Chess, Go, UNO, Poker, and more.

- **Package Name**: `aitabletop`
- **Version**: 0.1.0
- **License**: MIT
- **Python Requirements**: >= 3.11
- **Repository**: https://github.com/aitabletop/aitabletop-sdk

## Technology Stack

- **Language**: Python 3.11, 3.12, 3.13
- **HTTP Client**: `httpx` (>=0.27.0, <1.0.0)
- **WebSocket**: `websockets` (>=13.0, <15.0)
- **Optional**: `chess` (>=1.10.0, <2.0.0) for chess agents
- **Type Checking**: mypy (strict mode enabled)
- **Linting**: ruff
- **Testing**: pytest, pytest-asyncio

## Project Structure

```
aitabletop/
├── __init__.py           # Package exports and public API
├── client.py             # AITabletopClient - main API client
├── exceptions.py         # Custom exception classes
├── validators.py         # Input validation functions
├── memory_tracker.py     # Memory usage tracking utilities
├── testing.py            # Local testing utilities
└── agents/
    ├── __init__.py       # Agent module exports
    ├── base.py           # BaseAgent abstract class
    ├── random_agent.py   # RandomAgent implementation
    └── heuristic_chess.py # HeuristicChessAgent implementation

tests/
└── test_validators.py    # Unit tests for validators

.github/workflows/
├── python-package.yml    # CI: Test on Python 3.11/3.12/3.13
└── python-publish.yml    # CD: Publish to PyPI on release
```

## Key Components

### 1. AITabletopClient (`client.py`)
The main HTTP/WebSocket client for interacting with the AITabletop platform API.

Key methods:
- `register_agent(name, game_type)` - Register a new agent
- `join_queue(agent_id, game_type, ranked)` - Enter matchmaking queue
- `get_queue_status(queue_id)` - Poll for match assignment
- `play_match(match_id, agent)` - Connect via WebSocket and play
- `get_agent_stats(agent_id)` - Get agent rating and statistics
- `get_match_replay(match_id)` - Get game replay data

### 2. BaseAgent (`agents/base.py`)
Abstract base class that all agents must inherit from.

Required implementation:
```python
class MyAgent(BaseAgent):
    def act(self, observation: dict, time_limit_ms: int) -> dict:
        # Return dict with "move" key
        return {"move": "e2e4"}
```

### 3. Built-in Agents
- **RandomAgent**: Selects random legal moves (baseline)
- **HeuristicChessAgent**: Uses material counting for chess (requires `chess` package)

### 4. Validators (`validators.py`)
Comprehensive input validation for API keys, game types, agent names, match IDs, etc.

Supported games: `chess`, `go`, `uno`, `poker`, `tarot`, `san_juan`, `qwixx`

## Build and Development Commands

### Installation

```bash
# Basic installation
pip install -e .

# With development dependencies
pip install -e ".[dev]"

# With chess support
pip install -e ".[chess]"

# All extras
pip install -e ".[chess,dev,security]"
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_validators.py
```

### Code Quality

```bash
# Linting with ruff (configured in pyproject.toml)
ruff check aitabletop
ruff check --fix aitabletop

# Type checking with mypy
mypy aitabletop

# Security scanning (optional)
bandit -r aitabletop
safety check
```

## Code Style Guidelines

### Ruff Configuration (from `pyproject.toml`)
- **Target Python**: 3.11+
- **Line Length**: 100 characters
- **Enabled Rules**: E, F, I (isort), UP (pyupgrade), B (bugbear), S (security)
- **Ignored**: B008 (function call in argument default)

### Type Annotations
- Full type annotations required (mypy strict mode enabled)
- Use `from __future__ import annotations` for forward references
- Use modern syntax: `dict[str, Any]`, `list[str]`, `str | None`

### Docstrings
- Google-style docstrings with type hints
- Include security notes where applicable
- Document exceptions raised

### Naming Conventions
- **Classes**: PascalCase (e.g., `AITabletopClient`)
- **Functions/Methods**: snake_case (e.g., `register_agent`)
- **Constants**: UPPER_SNAKE_CASE
- **Private members**: Leading underscore (e.g., `_api_key`)

## Security Considerations

### API Key Management
- API keys must follow format: `at_live_xxxxxxxx` or `at_test_xxxxxxxx`
- Read from `AITABLETOP_API_KEY` environment variable (recommended)
- Never hardcode API keys in source code
- Keys are stored in memory only and never logged

### SSL/TLS
- SSL verification enabled by default (`verify_ssl=True`)
- Disabling SSL triggers a security warning
- Production URLs must use HTTPS

### Input Validation
- All user inputs validated before API calls
- API responses validated for required fields
- Error messages sanitized to prevent information leakage (truncated to 500 chars)

### Dependencies
- Pinned to specific version ranges in `pyproject.toml`
- Security extras available: `bandit`, `safety`

## Configuration Files

### pyproject.toml (Primary)
- Build system configuration
- Project metadata and dependencies
- Tool configurations (ruff, mypy, pytest)

### setup.py (Legacy Support)
- Duplicate configuration for backward compatibility
- Both files must be kept in sync

### .env.example
Template for environment variables:
```bash
AITABLETOP_API_KEY=at_test_your_api_key_here
AITABLETOP_BASE_URL=https://api.aitabletop.com
```

## CI/CD Pipeline

### python-package.yml (CI)
Triggered on push/PR to `main`:
1. Run on Python 3.11, 3.12, 3.13
2. Install dependencies with dev extras
3. Lint with flake8 (syntax errors only)
4. Run pytest

### python-publish.yml (CD)
Triggered on release publication:
1. Build distribution packages
2. Publish to PyPI using trusted publishing

## Testing Strategy

### Test Organization
- Tests located in `tests/` directory
- Test files named `test_*.py`
- Test classes named `Test*` (PascalCase)
- Test functions named `test_*` (snake_case)

### Current Test Coverage
- `test_validators.py`: Input validation functions
- Additional tests should cover client methods and agent implementations

### Testing Utilities
The `testing.py` module provides:
- `AgentTester`: Local agent testing framework
- `GameSimulator`: Local game simulation (requires external game implementations)
- `TestResult` / `TestReport`: Test result data classes

## Common Development Tasks

### Adding a New Agent
1. Create class in `aitabletop/agents/` inheriting from `BaseAgent`
2. Implement `act(observation, time_limit_ms)` method
3. Export from `aitabletop/agents/__init__.py`
4. Export from `aitabletop/__init__.py`
5. Add tests

### Adding a New Game
1. Add game name to `SUPPORTED_GAMES` in `validators.py`
2. Add validation logic if game-specific validation needed
3. Update documentation

### Adding New API Methods
1. Add method to `AITabletopClient` class
2. Add input validation using validators
3. Add response validation
4. Add appropriate error handling
5. Export any new exceptions from `__init__.py`
6. Add tests

## Important Notes

- The `main.py` file in the root is intentionally empty (excluded from package)
- Package includes `py.typed` marker for PEP 561 type hint support
- WebSocket connections use exponential backoff for reconnection (max 30s delay)
- Memory tracking available on Unix (resource module) or with psutil on Windows
- Error messages are intentionally sanitized to prevent information leakage
