"""
connector/client.py
───────────────────────────────────────────────────────────────────────────────
Connector: A unified OpenAI-compatible client for Sentinel.

Allows the Attack Runner and Re-tester to send requests either:
  1. Directly to the Victim App (http://localhost:8001)
  2. Through the Guard Gateway (http://localhost:8002)

Because both endpoints speak OpenAI /v1/chat/completions, switching targets
is as simple as changing the `base_url`.

Supports both synchronous and asynchronous calls, and measures request latency
(crucial for benchmarking Guard overhead).
───────────────────────────────────────────────────────────────────────────────
"""

import time
from typing import Any
import httpx

from .exceptions import (
    ConnectorAPIError,
    ConnectorConnectionError,
    ConnectorError,
    ConnectorTimeoutError,
)
from .models import ConnectorResponse


class Connector:
    """
    Client for interacting with OpenAI-compatible chat completion services.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        model: str = "llama3.2:1b",
        api_key: str = "sentinel-local",
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
        async_transport: httpx.AsyncBaseTransport | None = None,
    ):
        """
        Initialize the Connector.

        Args:
            base_url: Base URL of the target service (e.g. 'http://localhost:8001'
                      or 'http://localhost:8001/v1'). Trailing slashes are stripped.
            model: Default model identifier to send in requests.
            api_key: Optional authorization token (Bearer token).
            timeout: Maximum wait time in seconds for a response.
            transport: Optional custom HTTPX transport (useful for ASGI in-memory testing).
            async_transport: Optional custom async HTTPX transport.
        """
        self.base_url = self._normalize_url(base_url)
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport
        self.async_transport = async_transport

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Ensure endpoint URL ends with /v1/chat/completions."""
        cleaned = url.rstrip("/")
        if cleaned.endswith("/chat/completions"):
            return cleaned
        if cleaned.endswith("/v1"):
            return f"{cleaned}/chat/completions"
        return f"{cleaned}/v1/chat/completions"

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Sentinel-Connector/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra_params:
            payload.update(extra_params)
        return payload

    def _parse_response(self, resp: httpx.Response, latency_ms: float) -> ConnectorResponse:
        try:
            data = resp.json()
        except Exception as e:
            raise ConnectorAPIError(
                status_code=resp.status_code,
                message=f"Failed to parse JSON response: {e}",
                raw_response=resp.text,
            ) from e

        choices = data.get("choices", [])
        content = ""
        if choices and isinstance(choices, list):
            message = choices[0].get("message", {})
            content = message.get("content", "")

        return ConnectorResponse(
            content=content,
            raw=data,
            latency_ms=round(latency_ms, 2),
            status_code=resp.status_code,
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
        )

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """
        Send a synchronous chat completion request.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Optional model override.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Optional token cap.
            **kwargs: Extra parameters passed to the JSON payload.

        Returns:
            ConnectorResponse containing content, latency_ms, usage, and raw data.
        """
        payload = self._build_payload(messages, model, temperature, max_tokens, kwargs)
        headers = self._get_headers()

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                resp = client.post(self.base_url, headers=headers, json=payload)
        except httpx.ConnectError as e:
            raise ConnectorConnectionError(f"Cannot connect to target at {self.base_url}: {e}") from e
        except httpx.TimeoutException as e:
            raise ConnectorTimeoutError(f"Request timed out after {self.timeout}s to {self.base_url}") from e
        except Exception as e:
            raise ConnectorError(f"Unexpected connection error: {e}") from e

        elapsed_ms = (time.perf_counter() - start) * 1000

        if resp.status_code >= 400:
            raise ConnectorAPIError(
                status_code=resp.status_code,
                message=resp.text,
                raw_response=resp.text,
            )

        return self._parse_response(resp, elapsed_ms)

    async def achat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ConnectorResponse:
        """
        Send an asynchronous chat completion request.
        """
        payload = self._build_payload(messages, model, temperature, max_tokens, kwargs)
        headers = self._get_headers()

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.async_transport) as client:
                resp = await client.post(self.base_url, headers=headers, json=payload)
        except httpx.ConnectError as e:
            raise ConnectorConnectionError(f"Cannot connect to target at {self.base_url}: {e}") from e
        except httpx.TimeoutException as e:
            raise ConnectorTimeoutError(f"Request timed out after {self.timeout}s to {self.base_url}") from e
        except Exception as e:
            raise ConnectorError(f"Unexpected connection error: {e}") from e

        elapsed_ms = (time.perf_counter() - start) * 1000

        if resp.status_code >= 400:
            raise ConnectorAPIError(
                status_code=resp.status_code,
                message=resp.text,
                raw_response=resp.text,
            )

        return self._parse_response(resp, elapsed_ms)

    def check_health(self) -> dict[str, Any]:
        """
        Check health of the target service by calling its /health endpoint.
        """
        root_url = self.base_url.split("/v1/chat/completions")[0]
        health_url = f"{root_url}/health"

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(health_url)
            return {
                "ok": resp.status_code == 200,
                "status_code": resp.status_code,
                "data": resp.json() if resp.status_code == 200 else resp.text,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
