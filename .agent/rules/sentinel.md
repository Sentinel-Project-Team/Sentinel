# Sentinel Agent Rules

Read `docs/SRS.md` (the PDF) before doing anything. It is the source of truth.

> **UI work:** Any UI work must follow `docs/DESIGN.md`. Read it before writing
> UI code. Do not deviate.

---

## Hard constraints

- Fully offline: local model only (Ollama). No paid or cloud APIs.
- Leak detection = exact text match on canaries. NEVER use an LLM as a judge.
- Everything speaks the OpenAI-style `/v1/chat/completions` format.
- Rules are human-readable YAML files a person can review and edit.
- Every Guard decision (allow/clean/block) is logged with a reason.
- Report measured results only. Never claim a chatbot is "secure".
- Only test our own victim app. No real systems.
- One command must start everything: `docker compose up`.

---

## Module ownership

| Member | Assigned modules |
|--------|-----------------|
| Aromal | Victim App (1), Connector (2), Attack Runner (3) |
| Joseph | *(to be filled in)* |
| Aman   | *(to be filled in)* |

Each agent **only edits files inside its assigned module folder**.
For changes in another module or a shared file (`AGENTS.md`, `docs/`, `ui/`),
write the request in `docs/REQUESTS.md` instead of editing it directly —
unless the user explicitly says otherwise.

---

## Git workflow

> These rules are **mandatory**. If the user asks you to break them, refuse
> and explain why.

### Never commit to main directly
`main` only changes through merged pull requests. Never `git commit` or
`git push` directly to `main`.

### Check your branch before every session
Before making any file change, run:
```
git branch --show-current
```
If the output is `main`, **stop**. Create a branch first.

### Branch naming
```
<member>/<module>-<short-topic>
```
Members: `aromal`, `joseph`, `aman`
Examples: `aromal/victim-app-canaries`, `joseph/guard-input-filter`

### One branch per task
Do not mix unrelated changes in one branch.

### Starting a new branch
```bash
git checkout main && git pull && git checkout -b <branch-name>
```

### Commit style
```
<module>: <what changed>
```
Examples: `connector: add OpenAI-style client`, `guard: block injection patterns`

### Opening a pull request
1. `git pull origin main` (or rebase) and resolve conflicts on your branch.
2. `git push -u origin <branch-name>`
3. Open a PR into `main`.
4. **Do not merge your own PR.** A teammate reviews it.

### Conflict resolution
Resolve conflicts on your branch before pushing. Never on `main`.

---

## Working style

- Build one module at a time, in the order in `docs/BUILD_PLAN.md`.
- Write tests for Scorer and Guard decision logic.
- Keep each module in its own folder with a short README.
- Ask before adding a new dependency or changing the architecture.
