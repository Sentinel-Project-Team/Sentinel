"""
connector/exceptions.py
───────────────────────────────────────────────────────────────────────────────
Custom exceptions for Sentinel's Connector client.
───────────────────────────────────────────────────────────────────────────────
"""

class ConnectorError(Exception):
    """Base exception for all connector errors."""
    pass


class ConnectorConnectionError(ConnectorError):
    """Raised when the target endpoint is unreachable."""
    pass


class ConnectorTimeoutError(ConnectorError):
    """Raised when a request exceeds the configured timeout."""
    pass


class ConnectorAPIError(ConnectorError):
    """Raised when the target returns a 4xx or 5xx status code."""
    def __init__(self, status_code: int, message: str, raw_response: str | None = None):
        super().__init__(f"Target returned HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.raw_response = raw_response
