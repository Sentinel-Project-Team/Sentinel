# Sentinel: Project Context

Read docs/SRS.md (the PDF) before doing anything. It is the source of truth.

> **UI work:** Any UI work must follow docs/DESIGN.md. Read it before writing
> UI code. Do not deviate.

---

## What we're building

A test-and-protect tool for LLM chatbots. A Tester attacks a chatbot using
planted fake secrets ("canaries"); a Guard gateway sits in front of the chatbot
and allows/cleans/blocks messages; a Rule Maker converts successful attacks into
readable rule files; a Re-tester proves the improvement. Dashboard shows results.

---

## Hard constraints

- Fully offline: local model only (Ollama). No paid or cloud APIs.
- Leak detection = exact text match on canaries. NEVER use an LLM as a judge.
- Everything speaks the OpenAI-style /v1/chat/completions format, so the Guard
  is a drop-in proxy and the Tester can point at either the bot or the Guard.
- Rules are human-readable files (YAML) a person can review and edit.
- Every Guard decision (allow/clean/block) is logged with a reason.
- Report measured results only. Never claim a chatbot is "secure".
- Only test our own victim app. No real systems.
- One command must start everything (docker compose up).

---

## Modules

1 Victim app, 2 Connector, 3 Attack Runner, 4 Scorer, 5 Guard,
6 Rule Maker, 7 Re-tester, 8 Dashboard.

---

## Module ownership

| Member | Assigned modules |
|--------|-----------------|
| Aromal | *(reassigned — to be filled in)* |
| Joseph | *(to be filled in)* |
| Aman   | Victim App (1), Connector (2), Attack Runner (3) |

Each agent should **only edit files inside its assigned module folder**.
If a change is needed in another module or in a shared file (`AGENTS.md`,
`docs/`, `ui/`), write the request in `docs/REQUESTS.md` instead of editing
it directly — unless the user has explicitly said to do so.

---

## Working style

- Build one module at a time, in the order in docs/BUILD_PLAN.md.
- Write tests for Scorer and Guard decision logic.
- Keep each module in its own folder with a short README.
- Ask before adding a new dependency or changing the architecture.

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
If the output is `main`, **stop**. Create a branch first (see below).

### Branch naming
```
<member>/<module>-<short-topic>
```
- Members: `aromal`, `joseph`, `aman`
- Examples:
  - `aromal/victim-app-canaries`
  - `joseph/guard-input-filter`
  - `aman/dashboard-overview-page`

### One branch per task
Do not mix unrelated changes in one branch. Each task gets its own branch.

### Starting a new branch
Always start from the latest `main`:
```bash
git checkout main && git pull && git checkout -b <branch-name>
```

### Commit style
Commit small and often. Message format:
```
<module>: <what changed>
```
Examples:
- `connector: add OpenAI-style client`
- `guard: block prompt-injection patterns on input`
- `scorer: exact canary match returns LeakResult`

### Opening a pull request
When a task is done:
1. `git pull origin main` (or rebase on main) and resolve any conflicts on
   your branch — never on `main`.
2. Push the branch: `git push -u origin <branch-name>`
3. Open a PR into `main`.
4. **Do not merge your own PR.** A teammate reviews and merges it.

### Module boundaries
- Only edit files inside your assigned module folder.
- For changes needed in another module or in a shared file (`AGENTS.md`,
  `docs/`, `ui/`), write the request in `docs/REQUESTS.md` instead of
  editing the file directly — unless the user explicitly says otherwise.

### Conflict resolution
Resolve conflicts on your branch before pushing:
```bash
git pull origin main   # or: git rebase origin/main
# fix conflicts
git add .
git commit
git push
```
Never resolve conflicts directly on `main`.


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
If the output is `main`, **stop**. Create a branch first (see below).

### Branch naming
```
<member>/<module>-<short-topic>
```
- Members: `aromal`, `joseph`, `aman`
- Examples:
  - `aromal/victim-app-canaries`
  - `joseph/guard-input-filter`
  - `aman/dashboard-overview-page`

### One branch per task
Do not mix unrelated changes in one branch. Each task gets its own branch.

### Starting a new branch
Always start from the latest `main`:
```bash
git checkout main && git pull && git checkout -b <branch-name>
```

### Commit style
Commit small and often. Message format:
```
<module>: <what changed>
```
Examples:
- `connector: add OpenAI-style client`
- `guard: block prompt-injection patterns on input`
- `scorer: exact canary match returns LeakResult`

### Opening a pull request
When a task is done:
1. `git pull origin main` (or rebase on main) and resolve any conflicts on
   your branch — never on `main`.
2. Push the branch: `git push -u origin <branch-name>`
3. Open a PR into `main`.
4. **Do not merge your own PR.** A teammate reviews and merges it.

### Module boundaries
- Only edit files inside your assigned module folder.
- For changes needed in another module or in a shared file (`AGENTS.md`,
  `docs/`, `ui/`), write the request in `docs/REQUESTS.md` instead of
  editing the file directly — unless the user explicitly says otherwise.

### Conflict resolution
Resolve conflicts on your branch before pushing:
```bash
git pull origin main   # or: git rebase origin/main
# fix conflicts
git add .
git commit
git push
```
Never resolve conflicts directly on `main`.