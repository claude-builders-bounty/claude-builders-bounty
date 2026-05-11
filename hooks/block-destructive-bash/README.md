# block-destructive-bash

A Claude Code **PreToolUse** hook that intercepts `Bash` tool calls and blocks
known-destructive patterns (`rm -rf /`, `git push --force`, `git reset --hard`,
`DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`, `mkfs`, `dd of=/dev/sdX`,
`chmod 777`, fork bombs, `shutdown`/`reboot`, …) before they execute.

- Blocks with exit code **2** + a structured JSON `{"decision":"block","reason":"…"}` so Claude sees *why*.
- Logs every blocked attempt to `~/.claude/hooks/blocked.log` (JSON-lines: timestamp, project, reason, command).
- Configurable **allowlist** and **extra rules** via `~/.claude/hooks/block_destructive_bash.config.json`.
- No deps — pure Python 3 stdlib.

## Install (2 commands)

```sh
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/hooks/block-destructive-bash/install.sh
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py`
and registers it in `~/.claude/settings.json` under `hooks.PreToolUse` with
matcher `"Bash"`. Restart Claude Code (or start a new session) to pick it up.

## Verify

```sh
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}' \
  | python3 ~/.claude/hooks/block_destructive_bash.py; echo "exit=$?"
```

You should see a JSON `{"decision":"block",...}` and `exit=2`. A safe command
(`ls -la`) returns `exit=0` with no output.

## Configure

Create `~/.claude/hooks/block_destructive_bash.config.json`:

```json
{
  "allowlist": [
    "^rm -rf /tmp/[\\w./-]+$",
    "^rm -rf node_modules$",
    "^rm -rf \\.next$"
  ],
  "extra_rules": [
    ["\\bcurl\\s+.*\\|\\s*sh\\b", "piping curl into sh is dangerous"]
  ],
  "disabled_rules": []
}
```

- `allowlist`: regexes; if any matches the command, the hook returns 0 immediately.
- `extra_rules`: `[regex, reason]` pairs added to the default ruleset.
- `disabled_rules`: list of default-rule regex strings (copy-paste from
  `block_destructive_bash.py`) to turn off.

A starter config lives at `block_destructive_bash.config.example.json`.

## Default ruleset

| Category | Pattern (abbrev.) |
|---|---|
| Filesystem | `rm -rf …`, `mkfs`, `dd of=/dev/sdX`, `> /dev/sdX`, `chmod 777`, fork bomb |
| Git | `git push --force`/`-f`/`--force-with-lease`, `git reset --hard`, `git clean -f`, `git checkout .` |
| SQL | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM … (no WHERE)` |
| System | `shutdown`, `halt`, `poweroff`, `reboot` |

Patterns are case-insensitive and apply across heredocs / multi-line commands.

## Tests

```sh
python3 hooks/block-destructive-bash/tests/test_hook.py
```

33 cases cover blocks, allows, allowlist override, custom extra rules,
disabling default rules, and pass-through for non-Bash tools.

## Logs

```sh
tail -f ~/.claude/hooks/blocked.log
```

Each line is JSON: `{"timestamp": "...", "project": "...", "reason": "...", "command": "..."}`.

## How it fits Claude Code's hook protocol

- Reads the PreToolUse JSON payload from stdin (`tool_name`, `tool_input.command`, `cwd`).
- Non-`Bash` tools: exit 0 (pass through).
- Match found: prints `{"decision":"block","reason":"..."}` to stdout, the
  human reason to stderr, exits **2** (Claude Code convention: block + show
  stderr to the model).
- No match: exit 0.

Reference: <https://docs.anthropic.com/claude-code/hooks>
