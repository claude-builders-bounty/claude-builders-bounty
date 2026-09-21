# Block destructive Bash commands (Claude Code PreToolUse hook)

**Bounty:** [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — $100

Intercepts Claude Code `Bash` tool calls and **denies** destructive patterns before they run. Every denial is appended to `~/.claude/hooks/blocked.log`.

## Install (2 commands)

```bash
curl -fsSL https://raw.githubusercontent.com/masaki12214/claude-builders-bounty/feat/block-destructive-hook-masaki/hooks/block-destructive/install.sh -o /tmp/bd-install.sh
bash /tmp/bd-install.sh
```

Or from a local checkout of this folder:

```bash
cd hooks/block-destructive && bash install.sh
```

Requires: `python3` (stdlib only).

## What it blocks

| Pattern | Example |
|---------|--------|
| `rm -rf` / `rm -fr` / `rm --recursive --force` | `rm -rf /tmp/build` |
| `DROP TABLE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE audit_log;` |
| `git push --force` / `-f` / `--force-with-lease` | `git push --force origin main` |
| `DELETE FROM` **without** `WHERE` | `DELETE FROM sessions;` |

Safe commands (including `DELETE FROM t WHERE id=1`, `rm file.txt`, `git push origin main`) pass through unchanged.

## How it works

1. Claude Code fires `PreToolUse` for `Bash`.
2. `block_destructive.py` reads the tool JSON from stdin.
3. On match → writes JSON `permissionDecision: deny` + reason for Claude, and logs:
   `timestamp TAB rule TAB command TAB project_path` → `~/.claude/hooks/blocked.log`
4. On no match → exit 0 (normal permission flow).

## Project-local install

Copy `block_destructive.py` to `.claude/hooks/` and merge `settings.project.json` into `.claude/settings.json`.

## Tests

```bash
python3 hooks/block-destructive/tests/test_patterns.py
```

## Acceptance map (bounty #3)

| Criterion | How |
|-----------|-----|
| `~/.claude/hooks/` format | `install.sh` + `settings.json` |
| Blocks listed patterns | `RULES` in `block_destructive.py` |
| Logs timestamp, command, project path | `blocked.log` TSV lines |
| Clear message to Claude | `permissionDecisionReason` |
| Does not break normal Bash | allow tests in `tests/test_patterns.py` |
| README ≤ 2 install commands | This file |
