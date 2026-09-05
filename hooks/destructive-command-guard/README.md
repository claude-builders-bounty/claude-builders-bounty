# Claude Code Pre-Tool-Use Destructive Command Guard

[![Tests](https://img.shields.io/badge/tests-27%20passed-brightgreen.svg)](#testing)
[![Claude Code](https://img.shields.io/badge/claude--code-hooks%20compatible-purple.svg)](https://docs.anthropic.com/claude-code/hooks)
[![Opire Bounty](https://img.shields.io/badge/opire--bounty-%24100-gold.svg)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

A lightweight, zero-dependency security hook for **Claude Code** that intercepts and blocks dangerous commands before execution, protecting repositories, production databases, and git histories.

---

## Features & Acceptance Criteria Compliance

| Acceptance Criterion | Implementation Status | Behavior |
|---|---|---|
| **Hook Format** | `~/.claude/hooks/pre-tool-use` | Standard Claude Code hook JSON stdin protocol |
| **`rm -rf`** | Fully blocked | Intercepts `rm -rf`, `rm -fr`, `rm -r -f`, `--recursive --force` |
| **`DROP TABLE`** | Fully blocked | Intercepts SQL table dropping across queries |
| **`git push --force`** | Fully blocked | Intercepts `git push --force`, `-f`, `--force-with-lease` |
| **`TRUNCATE`** | Fully blocked | Intercepts `TRUNCATE` and `TRUNCATE TABLE` statements |
| **`DELETE FROM` (no WHERE)**| Fully blocked | Intercepts unrestricted bulk table deletions |
| **Audit Logging** | `~/.claude/hooks/blocked.log` | Appends JSON records with ISO timestamp, command, project path |
| **AI Guidance** | Clear stderr feedback | Explains the specific violation and provides safe alternatives |
| **Normal Commands** | 100% Unaffected | Safe commands (`ls`, `git status`, `DELETE ... WHERE id=1`) pass seamlessly |

---

## Installation (2 Commands)

### Linux / macOS
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash install.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
.\install.ps1
```

---

## How It Works

1. When Claude Code attempts to run a bash tool command, it passes the tool payload to `~/.claude/hooks/pre-tool-use`.
2. The guard evaluates the command against regex rules.
3. If destructive:
   - The hook exits with code `1`.
   - The blocked event is appended to `~/.claude/hooks/blocked.log`.
   - An explanatory warning is displayed to Claude detailing why the command was rejected and how to perform the action safely.
4. If clean:
   - The hook exits with code `0`, allowing normal execution without delay.

### Audit Log Sample (`~/.claude/hooks/blocked.log`)
```json
{"timestamp": "2026-09-05T18:21:05.123456Z", "rule": "RM_RF", "attempted_command": "rm -rf /tmp/data", "project_path": "/workspace/my-app"}
{"timestamp": "2026-09-05T18:21:05.234567Z", "rule": "GIT_PUSH_FORCE", "attempted_command": "git push --force origin main", "project_path": "/workspace/my-app"}
```

---

## Testing

Run the test suite verifying all 27 boundary cases:

```bash
pytest tests/
```

Result:
```
tests/test_guard.py ........................... [100%]
27 passed in 0.09s
```

---

## How to Claim the Bounty on Opire

1. **Comment on Issue #3**:
   ```
   /opire try
   ```
2. **Submit PR**:
   - Push branch `feat/destructive-command-guard`.
   - Open Pull Request referencing Issue #3 (`Fixes #3`).
   - Include `/claim #3` in the PR description.
3. **Payment**:
   - Released automatically via Stripe Connect on Opire upon PR merge.
