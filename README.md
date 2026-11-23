# Sentinel 🛡️

**A test-and-protect tool for LLM chatbots.**  
Attacks a chatbot with planted canary secrets, measures leakage exactly (no AI judge), auto-generates Guard rules, and proves before-and-after improvement.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Docker + Docker Compose | 24+ |
| Python (host only, for health check) | 3.11+ |
| ~8 GB free disk (Ollama model cache) | – |
| Internet access (first run only, to pull model) | – |

> After the first pull everything runs **fully offline**.

---

## One-command start

```bash
docker compose up
```

This will:
1. Start **Ollama** and pull `llama3.2:1b` (configurable via `SENTINEL_MODEL`)
2. Start the **Victim App** (chatbot with canary secrets) on port `8001`
3. Start the **Guard Gateway** (proxy) on port `8002`
4. Start the **Dashboard** on port `8080`

---

## Configuration

Copy `.env.example` to `.env` and edit as needed:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `SENTINEL_MODEL` | `llama3.2:1b` | Ollama model to use |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API base URL |

---

## Health check

After `docker compose up`, verify everything is running:

```bash
python scripts/health_check.py
```

Expected output:
```
[✓] Ollama reachable at http://localhost:11434
[✓] Model 'llama3.2:1b' is loaded
[✓] Victim app healthy at http://localhost:8001
[✓] Guard gateway healthy at http://localhost:8002
[✓] Dashboard healthy at http://localhost:8080
Sentinel is ready.
```

---

## Ports

| Service | Port | URL |
|---|---|---|
| Ollama | 11434 | http://localhost:11434 |
| Victim App | 8001 | http://localhost:8001 |
| Guard Gateway | 8002 | http://localhost:8002 |
| Dashboard | 8080 | http://localhost:8080 |

---

## Project layout

```
sentinel/
├── common/            # Shared Python library (Connector, DB schema, models)
├── victim/            # Test chatbot with canary secrets
├── guard/             # Gateway: inspect / allow / clean / block
├── runner/            # Attack runner + adaptive rewriter
├── scorer/            # Exact canary-match scoring
├── rule_maker/        # Convert successful attacks → YAML rules
├── retester/          # Before-and-after evaluation + metrics
├── dashboard/         # Web UI
├── data/
│   ├── attacks/       # Attack YAML files
│   └── harmless/      # Benign test questions
├── rules/             # Guard rule YAML files (human-editable)
├── scripts/           # Utility scripts (health check, etc.)
├── docs/              # SRS, build plan, architecture notes
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Module overview

| # | Module | Port | Purpose |
|---|---|---|---|
| 1 | Victim App | 8001 | Chatbot with planted canaries; demo target |
| 2 | Connector | (library) | OpenAI-style API client for any endpoint |
| 3 | Attack Runner | (CLI) | Sends attacks, records answers |
| 4 | Scorer | (library) | Exact canary-match leak detection |
| 5 | Guard | 8002 | Proxy gateway; allow / clean / block |
| 6 | Rule Maker | (CLI) | Attacks → YAML guard rules |
| 7 | Re-tester | (CLI) | Before-and-after evaluation |
| 8 | Dashboard | 8080 | Web UI with charts and live demo |

---

## Hard constraints (from AGENTS.md)

- **Fully offline** after first model pull.
- **Leak detection** = exact text match on canaries. Never an AI judge.
- **OpenAI-style API** everywhere — Guard is a drop-in proxy.
- **Human-readable YAML** rules a person can review and edit.
- **Every Guard decision** logged with a reason.
- **Only our own victim app** is ever tested.
- `docker compose up` starts everything.

---

## Development

Build the phase plan in [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md).  
See each module's own `README.md` for per-service setup.
