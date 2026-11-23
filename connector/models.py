"""
connector/models.py
───────────────────────────────────────────────────────────────────────────────
Data structures returned by Sentinel's Connector.
───────────────────────────────────────────────────────────────────────────────
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorResponse:
    """
    Standardized response from an OpenAI-compatible /v1/chat/completions endpoint.
    
    Attributes:
        content: The text content of the assistant message.
        raw: Full parsed JSON dictionary from the upstream service.
        latency_ms: Round-trip response latency in milliseconds.
        status_code: HTTP status code received (typically 200).
        model: Model identifier reported in the response.
        usage: Token usage dict (prompt_tokens, completion_tokens, total_tokens).
    """
    content: str
    raw: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    status_code: int = 200
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
