"""
connector/tests/test_connector.py
───────────────────────────────────────────────────────────────────────────────
Unit tests for Sentinel's Connector client.
───────────────────────────────────────────────────────────────────────────────
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx
from fastapi.testclient import TestClient

from connector import (
    Connector,
    ConnectorAPIError,
    ConnectorConnectionError,
    ConnectorError,
    ConnectorResponse,
    ConnectorTimeoutError,
)

# Also import victim app to test integration between Connector and Victim App!
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "victim"))
from main import app as victim_app, _state as victim_state
from system_prompt import build_system_prompt, load_canaries


MOCK_CHAT_RESPONSE = {
    "id": "chatcmpl-test12345",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "llama3.2:1b",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "This is a test response from the chatbot."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 12,
        "completion_tokens": 8,
        "total_tokens": 20
    }
}


class TestUrlNormalization:
    def test_strip_trailing_slash(self):
        c = Connector(base_url="http://localhost:8001/")
        assert c.base_url == "http://localhost:8001/v1/chat/completions"

    def test_append_v1_completions(self):
        c = Connector(base_url="http://localhost:8001")
        assert c.base_url == "http://localhost:8001/v1/chat/completions"

    def test_preserve_v1_base(self):
        c = Connector(base_url="http://localhost:8001/v1")
        assert c.base_url == "http://localhost:8001/v1/chat/completions"

    def test_already_full_path(self):
        c = Connector(base_url="http://localhost:8001/v1/chat/completions")
        assert c.base_url == "http://localhost:8001/v1/chat/completions"


class TestHeadersAndPayload:
    def test_headers_with_api_key(self):
        c = Connector(api_key="secret-key-123")
        headers = c._get_headers()
        assert headers["Authorization"] == "Bearer secret-key-123"
        assert headers["Content-Type"] == "application/json"

    def test_headers_without_api_key(self):
        c = Connector(api_key="")
        headers = c._get_headers()
        assert "Authorization" not in headers

    def test_build_payload(self):
        c = Connector(model="default-model")
        msgs = [{"role": "user", "content": "Hello"}]
        payload = c._build_payload(msgs, model="custom-model", temperature=0.2, max_tokens=50)
        assert payload["model"] == "custom-model"
        assert payload["temperature"] == 0.2
        assert payload["max_tokens"] == 50
        assert payload["messages"] == msgs


class TestSyncChatCompletion:
    @patch("httpx.Client.post")
    def test_successful_completion(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_CHAT_RESPONSE
        mock_post.return_value = mock_resp

        c = Connector(base_url="http://localhost:8001")
        resp = c.chat_completion([{"role": "user", "content": "Hello"}])

        assert isinstance(resp, ConnectorResponse)
        assert resp.content == "This is a test response from the chatbot."
        assert resp.status_code == 200
        assert resp.model == "llama3.2:1b"
        assert resp.usage["total_tokens"] == 20
        assert resp.latency_ms >= 0.0

    @patch("httpx.Client.post")
    def test_api_error_raised_on_4xx_5xx(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        c = Connector(base_url="http://localhost:8001")
        with pytest.raises(ConnectorAPIError) as exc_info:
            c.chat_completion([{"role": "user", "content": "Hello"}])
        assert exc_info.value.status_code == 500

    @patch("httpx.Client.post")
    def test_connection_error_raised(self, mock_post):
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        c = Connector(base_url="http://localhost:8001")
        with pytest.raises(ConnectorConnectionError):
            c.chat_completion([{"role": "user", "content": "Hello"}])

    @patch("httpx.Client.post")
    def test_timeout_error_raised(self, mock_post):
        mock_post.side_effect = httpx.TimeoutException("Timed out")

        c = Connector(base_url="http://localhost:8001")
        with pytest.raises(ConnectorTimeoutError):
            c.chat_completion([{"role": "user", "content": "Hello"}])


class TestAsyncChatCompletion:
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_async_successful_completion(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_CHAT_RESPONSE
        mock_post.return_value = mock_resp

        c = Connector(base_url="http://localhost:8001")
        resp = await c.achat_completion([{"role": "user", "content": "Hello"}])

        assert isinstance(resp, ConnectorResponse)
        assert resp.content == "This is a test response from the chatbot."
        assert resp.status_code == 200
        assert resp.latency_ms >= 0.0


class TestCheckHealth:
    @patch("httpx.Client.get")
    def test_check_health_ok(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok", "service": "victim"}
        mock_get.return_value = mock_resp

        c = Connector(base_url="http://localhost:8001")
        health = c.check_health()
        assert health["ok"] is True
        assert health["data"]["status"] == "ok"


class TestConnectorVictimAppIntegration:
    """Smoke test: prove Connector communicates properly with the Victim App schema."""

    @pytest.mark.asyncio
    async def test_connector_talking_to_victim_app_async(self):
        # Setup victim state
        canaries_path = Path(__file__).parent.parent.parent / "victim" / "canaries.yaml"
        canaries = load_canaries(canaries_path)
        victim_state["canaries"] = canaries
        victim_state["system_prompt"] = build_system_prompt(canaries)

        # Mock Ollama response inside victim app
        mock_ollama_resp = {
            "model": "llama3.2:1b",
            "message": {
                "role": "assistant",
                "content": "Nexus Corp policy requires 2 weeks advance notice for leave.",
            },
            "done": True,
            "prompt_eval_count": 50,
            "eval_count": 15,
        }

        with patch("main._call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = mock_ollama_resp
            async_transport = httpx.ASGITransport(app=victim_app)
            connector = Connector(base_url="http://localhost:8001", async_transport=async_transport)
            res = await connector.achat_completion(
                messages=[{"role": "user", "content": "What is the leave policy?"}]
            )

            assert res.status_code == 200
            assert "Nexus Corp policy" in res.content
            assert res.model == "llama3.2:1b"
            assert res.latency_ms >= 0.0

    def test_connector_talking_to_victim_app_sync(self):
        # Test sync with MockTransport simulating victim response
        victim_response = {
            "id": "chatcmpl-victim123",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "llama3.2:1b",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Nexus Corp policy requires 2 weeks advance notice for leave."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 15, "total_tokens": 65}
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=victim_response)

        transport = httpx.MockTransport(handler)
        connector = Connector(base_url="http://localhost:8001", transport=transport)
        res = connector.chat_completion(
            messages=[{"role": "user", "content": "What is the leave policy?"}]
        )

        assert res.status_code == 200
        assert "Nexus Corp policy" in res.content
        assert res.model == "llama3.2:1b"
        assert res.latency_ms >= 0.0
