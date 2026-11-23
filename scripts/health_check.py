#!/usr/bin/env python3
"""
scripts/health_check.py
-----------------------
Sentinel Phase-0 health check.

Verifies:
  1. Ollama is reachable.
  2. The configured model is present in Ollama's model list.
  3. The Victim App, Guard, and Dashboard respond to their /health endpoints.

Usage:
    python scripts/health_check.py [--ollama-url URL] [--model MODEL]

Exit codes:
    0  – all checks passed
    1  – one or more checks failed
"""

import argparse
import os
import sys
import urllib.request
import urllib.error
import json

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}[✓]{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}[✗]{RESET} {msg}")


def check_url(label: str, url: str, timeout: int = 10) -> bool:
    """Return True if URL returns HTTP 2xx."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if 200 <= resp.status < 300:
                ok(f"{label} healthy at {url}")
                return True
            fail(f"{label} returned HTTP {resp.status} at {url}")
            return False
    except urllib.error.URLError as exc:
        fail(f"{label} unreachable at {url}: {exc.reason}")
        return False
    except Exception as exc:  # noqa: BLE001
        fail(f"{label} check failed ({url}): {exc}")
        return False


def check_ollama_model(ollama_url: str, model: str, timeout: int = 10) -> bool:
    """Return True if the named model appears in Ollama's /api/tags list."""
    tags_url = f"{ollama_url}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        models = [m.get("name", "") for m in data.get("models", [])]
        # Ollama names look like "llama3.2:1b"; also accept prefix match.
        matched = any(m == model or m.startswith(model.split(":")[0]) for m in models)
        if matched:
            ok(f"Model '{model}' is loaded (available: {', '.join(models)})")
            return True
        fail(
            f"Model '{model}' not found. Available: {models or 'none'}. "
            f"Run: docker compose exec ollama ollama pull {model}"
        )
        return False
    except urllib.error.URLError as exc:
        fail(f"Ollama unreachable at {tags_url}: {exc.reason}")
        return False
    except Exception as exc:  # noqa: BLE001
        fail(f"Ollama model check failed: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Sentinel health check")
    parser.add_argument(
        "--ollama-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama base URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("SENTINEL_MODEL", "llama3.2:1b"),
        help="Model name to verify (default: llama3.2:1b)",
    )
    parser.add_argument(
        "--skip-services",
        action="store_true",
        help="Only check Ollama; skip Victim/Guard/Dashboard",
    )
    args = parser.parse_args()

    print("── Sentinel Health Check ──────────────────────────────")
    results: list[bool] = []

    # 1. Ollama reachability
    ollama_ok = check_url("Ollama", f"{args.ollama_url}/api/tags")
    results.append(ollama_ok)

    # 2. Model presence (only if Ollama is up)
    if ollama_ok:
        results.append(check_ollama_model(args.ollama_url, args.model))
    else:
        fail("Skipping model check (Ollama unreachable)")
        results.append(False)

    if not args.skip_services:
        # 3. Victim App
        results.append(check_url("Victim App", "http://localhost:8001/health"))
        # 4. Guard Gateway
        results.append(check_url("Guard Gateway", "http://localhost:8002/health"))
        # 5. Dashboard
        results.append(check_url("Dashboard", "http://localhost:8080/health"))

    print("───────────────────────────────────────────────────────")
    if all(results):
        print(f"{GREEN}Sentinel is ready.{RESET}")
        return 0
    failed = results.count(False)
    print(f"{RED}{failed} check(s) failed. See above for details.{RESET}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
