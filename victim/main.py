"""
victim/main.py
───────────────────────────────────────────────────────────────────────────────
The Victim App — a deliberately vulnerable company chatbot for Sentinel testing.

What it does:
  - Exposes /v1/chat/completions in OpenAI format so the Attack Runner and
    Guard can point at it without caring it's Ollama underneath.
  - Injects canary secrets into the system prompt at startup. Those secrets
    can only appear in a response if the model was tricked into revealing them.
  - Exposes /health so Docker Compose knows when it's ready.
  - Exposes /v1/models so any OpenAI-compatible client recognises it.

Why OpenAI format?
  The whole system speaks one API shape. The Guard is a drop-in proxy in
  front of this app — it receives the same request format and forwards to
  the same format here. The Attack Runner doesn't need to know what's behind
  the endpoint. That's the entire point.
───────────────────────────────────────────────────────────────────────────────
"""

import os
import time
import uuid
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from system_prompt import build_system_prompt, load_canaries

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [victim] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config (from environment, with safe defaults for local dev) ───────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME      = os.getenv("SENTINEL_MODEL", "llama3.2:1b")
PORT            = int(os.getenv("PORT", "8001"))
# How long to wait for Ollama to respond (seconds).
# Small local models can be slow on first token.
OLLAMA_TIMEOUT  = float(os.getenv("OLLAMA_TIMEOUT", "120"))

# ── App state (populated at startup) ─────────────────────────────────────────
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load canaries and build system prompt once at startup."""
    canaries_path = Path(__file__).parent / "canaries.yaml"
    canaries = load_canaries(canaries_path)
    system_prompt = build_system_prompt(canaries)

    _state["canaries"]      = canaries
    _state["system_prompt"] = system_prompt

    log.info("Victim app starting — model: %s, Ollama: %s", MODEL_NAME, OLLAMA_BASE_URL)
    log.info("Loaded %d canaries: %s", len(canaries), [c["id"] for c in canaries])
    # Log canary values at DEBUG so they don't appear in production logs.
    for c in canaries:
        log.debug("  Canary %s = %r", c["id"], c["value"])

    yield

    log.info("Victim app shutting down.")


app = FastAPI(
    title="Sentinel Victim App",
    description=(
        "A deliberately vulnerable chatbot with planted canary secrets. "
        "Used as the attack target for Sentinel's tester and guard."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ── OpenAI-compatible request/response models ─────────────────────────────────

class ChatMessage(BaseModel):
    role: str                    # "system" | "user" | "assistant"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(default=MODEL_NAME)
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None)
    stream: bool = Field(default=False)


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prepend_system_prompt(messages: list[ChatMessage]) -> list[ChatMessage]:
    """
    Inject the canary-laden system prompt as the first message.

    If the caller already sent a system message, we prepend ours before it.
    This guarantees canaries are always in context even if the caller tries
    to override the system role.
    """
    sentinel_system = ChatMessage(
        role="system",
        content=_state["system_prompt"],
    )
    # Strip any existing system message from the caller — the victim app
    # controls its own system prompt.
    user_messages = [m for m in messages if m.role != "system"]
    return [sentinel_system, *user_messages]


async def _call_ollama(messages: list[ChatMessage], temperature: float) -> dict:
    """
    Forward the conversation to Ollama and return the raw Ollama response dict.

    Ollama's /api/chat endpoint uses a slightly different shape from OpenAI:
      - Request:  { model, messages, stream, options }
      - Response: { model, message: {role, content}, done, ... }

    We translate both directions so the rest of the system only sees
    the OpenAI format.
    """
    payload = {
        "model":   MODEL_NAME,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream":  False,
        "options": {"temperature": temperature},
    }

    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Cannot reach Ollama at {OLLAMA_BASE_URL}. "
                    "Is 'docker compose up ollama' running?"
                ),
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail=f"Ollama timed out after {OLLAMA_TIMEOUT}s.",
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama returned {exc.response.status_code}: {exc.response.text}",
            )

    return resp.json()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """
    Docker Compose and the health check script poll this.
    Returns 200 as soon as the app is up and canaries are loaded.
    """
    return {
        "status": "ok",
        "service": "victim",
        "model": MODEL_NAME,
        "ollama_url": OLLAMA_BASE_URL,
        "canaries_loaded": len(_state.get("canaries", [])),
    }


@app.get("/v1/models")
async def list_models():
    """
    Minimal OpenAI-compatible /v1/models response.
    Lets any OpenAI client recognise this endpoint without errors.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": 0,
                "owned_by": "sentinel-victim",
            }
        ],
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(req: ChatCompletionRequest):
    """
    OpenAI-compatible chat endpoint.

    Flow:
      1. Prepend the canary-laden system prompt (always, even if caller sent one).
      2. Forward to Ollama /api/chat.
      3. Translate Ollama's response back to OpenAI format.
      4. Return.

    The Guard will sit in front of this endpoint: it receives the same request
    format, optionally modifies it, forwards here, then inspects the response
    before returning it to the caller.
    """
    if req.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not supported in Phase 1. Set stream=false.",
        )

    # 1. Inject system prompt with canaries
    full_messages = _prepend_system_prompt(req.messages)
    log.info(
        "chat request — %d user message(s), temperature=%.2f",
        len(req.messages),
        req.temperature,
    )

    # 2. Call Ollama
    ollama_resp = await _call_ollama(full_messages, req.temperature)

    # 3. Translate to OpenAI format
    assistant_content = ollama_resp.get("message", {}).get("content", "")
    # Rough token estimate — Ollama gives eval_count / prompt_eval_count
    prompt_tokens     = ollama_resp.get("prompt_eval_count", 0)
    completion_tokens = ollama_resp.get("eval_count", 0)

    response = ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=MODEL_NAME,
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessage(role="assistant", content=assistant_content),
                finish_reason="stop",
            )
        ],
        usage=ChatUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )

    log.info(
        "chat response — %d completion tokens, finish_reason=stop",
        completion_tokens,
    )
    return response


@app.get("/debug/system-prompt")
async def debug_system_prompt():
    """
    Dev-only endpoint: shows the full system prompt including canary values.
    MUST be disabled (or firewalled) before any real deployment.
    Only accessible when DEBUG=true in environment.
    """
    if os.getenv("DEBUG", "false").lower() != "true":
        raise HTTPException(
            status_code=403,
            detail="Set DEBUG=true in the environment to use this endpoint.",
        )
    return {
        "system_prompt": _state.get("system_prompt", ""),
        "canaries": _state.get("canaries", []),
    }


# ── Entrypoint (for local dev without Docker) ─────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
