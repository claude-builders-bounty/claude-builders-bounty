# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands **before** they execute, blocks them, and explains why to Claude. Resolves [bounty #3 ($100)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

## What it blocks

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` / `rm -fr` (incl. absolute paths) | `rm -rf /tmp/foo` | Recursive force delete |
| `DROP TABLE/DATABASE/SCHEMA/INDEX/VIEW` | `DROP TABLE users` | Irreversible data loss |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Wipes table |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` | Mass delete |
| `git push --force` / `-f` | `git push -f origin main` | Rewrites remote history |

Everything else (normal `ls`, `cd`, `npm install`, `git status`, etc.) passes through.

## File layout

```
HOOK_3_block_destructive/
├── pre-tool-use-block-destructive.py   # main hook (Python 3.7+)
├── README.md                            # this file
└── samples/
    └── test-payload.json                # test fixture

scripts/
└── install_pre_tool_use_block_destructive.sh   # one-command installer

tests/
├── __init__.py
└── test_pre_tool_use_block_destructive.py      # 20 unit tests

examples/
└── blocked-command-output.json                   # example decision JSON
```

## Installation (2 commands or fewer)

```bash
# Option A: one-shot installer (auto-registers in ~/.claude/settings.json)
bash scripts/install_pre_tool_use_block_destructive.sh

# Option B: manual
mkdir -p ~/.claude/hooks
cp HOOK_3_block_destructive/pre-tool-use-block-destructive.py ~/.claude/hooks/
# Then add to ~/.claude/settings.json:
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"}
        ]
      }
    ]
  }
}
```

Restart Claude Code. The hook activates on the next bash command.

## How it works

When Claude tries to run a blocked command:
1. The hook receives the JSON payload from Claude Code via stdin
2. The command is matched against compiled regex patterns
3. If matched, the hook writes a `BLOCKED:` entry to `~/.claude/hooks/blocked.log` (with timestamp, command, project path) and prints `{"decision": "block", "reason": "..."}` to stdout
4. Claude receives a clear explanation and can ask the user for confirmation

## Testing

### Unit tests (20 tests, ~7ms)

```bash
python -m unittest tests.test_pre_tool_use_block_destructive -v
```

### Manual test (pipe a fake Claude Code payload)

```bash
# Should block:
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"},"cwd":"/tmp"}' \
  | python3 HOOK_3_block_destructive/pre-tool-use-block-destructive.py
# → {"decision": "block", "reason": "Blocked by pre-tool-use-block-destructive: recursive force delete (rm -rf) on absolute path.\n..."}

# Should allow:
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' \
  | python3 HOOK_3_block_destructive/pre-tool-use-block-destructive.py
# → no output (exit 0)
```

## Log format

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-06-18T08:58:42.578780] BLOCKED: recursive force delete (rm -rf) on absolute path
  command: rm -rf /tmp/foo
  project: /tmp

[2026-06-18T08:58:42.699321] BLOCKED: SQL DROP statement
  command: DROP TABLE users;
  project: /tmp
```

## Verification done

- ✅ 20/20 unittest pass
- ✅ Installer tested on Windows Git Bash + macOS/Linux-compatible
- ✅ Installer is idempotent (re-running doesn't duplicate the entry)
- ✅ Manual test with 6+ command scenarios
- ✅ Pure Python stdlib (no third-party deps)
- ✅ Python 3.7+ compatible

## Dependencies

- Python 3.7+ on `PATH` (`python3`, `python`, or Windows `py`)
- That's it. No pip packages.

## Customization

Edit `BLOCKED_PATTERNS` in `pre-tool-use-block-destructive.py` to add/remove patterns. Format: `(regex, human-readable-reason)`.

## License

MIT
