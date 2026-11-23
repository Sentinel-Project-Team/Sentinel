"""
connector package
───────────────────────────────────────────────────────────────────────────────
Unified OpenAI-compatible connector for Sentinel.
───────────────────────────────────────────────────────────────────────────────
"""

from .client import Connector
from .exceptions import (
    ConnectorAPIError,
    ConnectorConnectionError,
    ConnectorError,
    ConnectorTimeoutError,
)
from .models import ConnectorResponse

__all__ = [
    "Connector",
    "ConnectorResponse",
    "ConnectorError",
    "ConnectorConnectionError",
    "ConnectorTimeoutError",
    "ConnectorAPIError",
]
