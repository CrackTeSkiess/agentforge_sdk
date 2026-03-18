# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of the AgentForge SDK seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do NOT report security issues through public GitHub issues.**

Instead, please report them via email to [security@agentforge.io](mailto:security@agentforge.io) with the following information:

1. Description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact
4. Suggested fix (if any)

You should receive a response within 48 hours. If for some reason you do not, please follow up.

## Security Best Practices

### API Key Management

The SDK requires an API key for authentication. Follow these best practices:

1. **Never hardcode API keys in source code** - Use environment variables:
   ```python
   import os
   from agentforge import RLArenaClient

   client = RLArenaClient(api_key=os.environ.get("RL_ARENA_API_KEY"))
   ```

2. **Use environment variables** - Set the `RL_ARENA_API_KEY` environment variable:
   ```bash
   export RL_ARENA_API_KEY="rla_live_xxxxxxxx"
   ```

3. **Use separate keys for development and production** - Use `rla_test_` prefixed keys for testing

4. **Rotate keys regularly** - Periodically regenerate API keys

### SSL/TLS Configuration

The SDK enforces SSL/TLS by default:

```python
# Production (default) - SSL verification enabled
client = RLArenaClient(api_key="your_key")

# Development only - SSL verification can be disabled for local testing
# WARNING: Never use in production
client = RLArenaClient(
    api_key="your_key",
    verify_ssl=False,  # Only for local development with self-signed certs
    base_url="http://localhost:8000"
)
```

### Memory Tracking

The SDK includes memory tracking to prevent resource exhaustion:

```python
from agentforge import MemoryTracker

tracker = MemoryTracker()
if tracker.is_tracking_available():
    print("Memory tracking is available")
else:
    print("WARNING: Memory tracking not available - install psutil for better tracking")
```

### Network Security

1. **Always use HTTPS** in production environments
2. **Verify SSL certificates** - Never disable SSL verification in production
3. **Use firewall rules** to restrict outbound connections if possible

### Code Security

1. **Keep the SDK updated** - Regular updates include security patches
2. **Review agent code** - Ensure custom agents don't expose sensitive data
3. **Limit agent permissions** - Use the minimum required permissions

## Security Features in AgentForge

### Input Validation
All user inputs are validated before being sent to the API:
- API key format validation
- Agent name sanitization
- Match ID format validation
- URL format validation

### Error Handling
Error messages are sanitized to prevent information leakage:
- Error details are truncated to 500 characters
- Internal error messages are not exposed

### Dependency Management
Dependencies are pinned to specific version ranges to prevent supply chain attacks:
```toml
dependencies = [
    "httpx>=0.27.0,<1.0.0",
    "websockets>=13.0,<15.0",
]
```

## Security Audit Checklist

When deploying the AgentForge SDK, verify:

- [ ] API keys are stored in environment variables, not source code
- [ ] SSL verification is enabled (`verify_ssl=True`)
- [ ] Using HTTPS for all production connections
- [ ] Dependencies are up to date
- [ ] Memory tracking is available (psutil installed)
- [ ] Custom agent code doesn't log or expose API keys
- [ ] Firewall rules restrict outbound connections if needed

## Known Limitations

1. **WebSocket Authentication**: The SDK uses header-based authentication for WebSocket connections. While transmitted over TLS, consider this when deploying in high-security environments.

2. **Memory Tracking**: On some platforms, memory tracking may not be available. The SDK will warn if this is the case.

3. **Error Information**: Error messages from the server are truncated to prevent information leakage, which may make debugging more difficult.

## Security Updates

Security updates will be released as patch versions (e.g., 0.1.1, 0.1.2). Subscribe to our release notifications to stay informed.

## Acknowledgments

We would like to thank the following for their contributions to our security:

- All security researchers who responsibly disclose vulnerabilities
- The Python security community
- Our dependencies' maintainers

## Contact

For security-related questions or concerns, contact us at [security@agentforge.io](mailto:security@agentforge.io).