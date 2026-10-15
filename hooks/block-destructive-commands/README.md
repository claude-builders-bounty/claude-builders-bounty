# PreToolUse hook: block destructive Bash commands

A Claude Code **PreToolUse** hook that intercepts dangerous shell / SQL commands
**before** they run, tells Claude why they were blocked, and appends an audit
line to `~/.claude/hooks/blocked.log`.

## What it blocks

| Pattern | Notes |
|---------|--------|
| `rm -rf` | Also `-fr`, `-r -f`, `--recursive --force`, optional `sudo` |
| `DROP TABLE` | Case-insensitive |
| `TRUNCATE` / `TRUNCATE TABLE` | Case-insensitive |
| `git push --force` | Also `-f`, `--force-with-lease` |
| `DELETE FROM` without `WHERE` | Per statement (`;`-split); `DELETE FROM t WHERE …` is allowed |

Normal Bash (`ls`, `git status`, `npm test`, `DELETE FROM t WHERE id=1`, …) is not blocked.

## Install (≤ 2 commands)

From a clone of this repository:

```bash
bash hooks/block-destructive-commands/install.sh
```

Or one-liner without a full clone:

```bash
git clone --depth 1 https://github.com/claude-builders-bounty/claude-builders-bounty.git /tmp/cbb && bash /tmp/cbb/hooks/block-destructive-commands/install.sh
```

The installer copies the hook into `~/.claude/hooks/`, merges a `PreToolUse` /
`Bash` entry into `~/.claude/settings.json` (keeps a `.bak`), and runs a
quick self-test. Requires **Python 3** (stdlib only).

### Manual install (also 2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-commands/block_destructive.py hooks/block-destructive-commands/block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh ~/.claude/hooks/block_destructive.py
```

Then add the contents of `settings.snippet.json` under `"hooks"` in
`~/.claude/settings.json` (or merge with the snippet's `PreToolUse` entry).

## Log format

Every blocked attempt appends one line to `~/.claude/hooks/blocked.log`:

```text
2026-10-15T10:31:00Z | rm -rf | /home/you/my-project | rm -rf /tmp/build
```

Fields: **timestamp (UTC)** · **matched pattern** · **project path (`cwd`)** · **attempted command**.

## How it works

Claude Code sends PreToolUse JSON on stdin (see
[Hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks)).
This hook:

1. Reads `tool_input.command` for Bash tool calls
2. If a destructive pattern matches → writes the log line and prints:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "…"
  }
}
```

3. Otherwise exits `0` with no output so the normal permission flow continues

## Self-test

```bash
bash hooks/block-destructive-commands/test/run-tests.sh
```

## Files

| File | Role |
|------|------|
| `block_destructive.py` | Detector + logger + JSON deny |
| `block-destructive.sh` | Thin launcher for Claude Code |
| `install.sh` | Copy + merge settings + self-test |
| `settings.snippet.json` | Hook registration snippet |
| `test/run-tests.sh` | Block / allow regression checks |
