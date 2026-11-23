# Connector

The client library that connects Sentinel's Attack Runner, Re-tester, and
evaluators to any OpenAI-compatible `/v1/chat/completions` endpoint.

## Purpose

Sentinel tests chatbots both **directly** (Victim App) and **protected**
(Guard Gateway proxy). Because both services expose standard OpenAI-style
interfaces, the Connector abstracts network transport, error handling,
URL normalization, and latency measurement into a single reusable client.

```
┌─────────────────┐
│  Attack Runner  │
│  or Re-tester   │
└────────┬────────┘
         │ calls chat_completion()
         ▼
┌─────────────────┐
│    Connector    │
└────────┬────────┘
         │ POST /v1/chat/completions
         ├───────────────────────────────┐
         ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│    Victim App    │           │  Guard Gateway   │
│ (localhost:8001) │           │ (localhost:8002) │
└──────────────────┘           └──────────────────┘
```

## Features

- **OpenAI-Compatible:** Standard `messages` payload with role/content dicts.
- **URL Normalization:** Handles `http://host:port`, `http://host:port/v1`, or trailing slashes automatically.
- **Sync & Async Support:** `chat_completion()` and `achat_completion()`.
- **Latency Tracking:** Measures round-trip time (`latency_ms`) on every call.
- **Typed Exceptions:**
  - `ConnectorConnectionError` (endpoint unreachable)
  - `ConnectorTimeoutError` (request timed out)
  - `ConnectorAPIError` (HTTP 4xx / 5xx with status and body)
- **Health Verification:** `check_health()` checks the target `/health` route.

## Usage

```python
from connector import Connector

# Point to Victim App
client = Connector(base_url="http://localhost:8001", model="llama3.2:1b")

# Point to Guard Gateway instead (same code!)
# client = Connector(base_url="http://localhost:8002", model="llama3.2:1b")

response = client.chat_completion(
    messages=[{"role": "user", "content": "What is the annual leave policy?"}],
    temperature=0.7,
)

print(response.content)      # "Nexus Corp employees get 18 days..."
print(response.latency_ms)   # 142.5 (ms)
print(response.status_code)  # 200
```

### Async Usage

```python
import asyncio
from connector import Connector

async def main():
    client = Connector(base_url="http://localhost:8001")
    response = await client.achat_completion(
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(response.content)

asyncio.run(main())
```

## Running Tests

```bash
pytest connector/tests/ -v
```
All tests mock network responses and run offline without dependencies on external services.
