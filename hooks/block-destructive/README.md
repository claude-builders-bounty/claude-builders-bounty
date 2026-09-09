# block-destructive — Claude Code PreToolUse hook

Intercepts dangerous bash commands before Claude Code executes them.

**Blocks:** `rm -rf` · `DROP TABLE` · `TRUNCATE` · `git push --force` · `DELETE FROM` without a `WHERE` clause

**Logs** every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, pattern, project path, and the full command.

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
bash claude-builders-bounty/hooks/block-destructive/install.sh
```

(or, if you already have the files: `bash install.sh` — one command)

The installer copies `pre-tool-use.py` into `~/.claude/hooks/` and registers the
hook in `~/.claude/settings.json` without clobbering existing hook config.

## How it works

- Reads the Claude Code hook JSON payload from stdin
- Only inspects `tool_name == "Bash"`; all other tools pass through untouched
- On a match, replies with a `deny` decision + a clear reason for Claude, and appends a log line
- On any unreadable input, exits without blocking (fail-open, never breaks normal commands)

## Test it manually

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/demo"}' | python3 pre-tool-use.py
# → deny + "Blocked destructive command pattern (rm -rf ...)"
cat ~/.claude/hooks/blocked.log
```
