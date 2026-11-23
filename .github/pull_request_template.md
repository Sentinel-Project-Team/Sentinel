---
name: pull-request-template
---

## What changed
<!-- One paragraph summary of what this PR does -->


## Module
<!-- Which module(s) does this PR touch? -->
- [ ] Victim App
- [ ] Connector
- [ ] Attack Runner
- [ ] Scorer
- [ ] Guard
- [ ] Rule Maker
- [ ] Re-tester
- [ ] Dashboard
- [ ] Shared / infra (AGENTS.md, docs/, docker-compose, scripts)

## Checklist
- [ ] I described what changed above
- [ ] All changes are inside my assigned module folder (or I got explicit permission)
- [ ] If I changed UI: I followed `docs/DESIGN.md`
- [ ] Tests run: `pytest <module>/tests/` passes (or N/A — explain why)
- [ ] Module `README.md` updated if the public interface changed
- [ ] No edits outside my assigned module (or cross-module changes are listed below)
- [ ] I did **not** merge this PR myself — a teammate will review

## Cross-module changes (if any)
<!-- List any file touched outside your module and why it was necessary -->


## How to test
<!-- Steps a reviewer can follow to verify this PR -->
1.
2.
