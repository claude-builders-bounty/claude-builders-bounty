# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands **before** they execute, blocks them, and explains why to Claude.

## What it blocks

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` / `rm -fr` | `rm -rf /tmp/foo` | Recursive force delete |
| `DROP TABLE/DATABASE/SCHEMA/INDEX/VIEW` | `DROP TABLE users` | Irreversible data loss |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Wipes table |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` | Mass delete |
| `git push --force` / `-f` | `git push -f origin main` | Rewrites remote history |

Everything else (normal `ls`, `cd`, `npm install`, `git status`, etc.) passes through.

## How it works

When Claude tries to run a blocked command:
1. The hook receives the JSON payload from Claude Code
2. The command is matched against the regex patterns
3. If matched, the hook writes a `BLOCKED:` entry to `~/.claude/hooks/blocked.log` and returns a `decision: block` JSON to Claude
4. Claude receives a clear explanation and can ask the user for confirmation

## Installation (2 steps)

### Step 1: Copy the hook

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use-block-destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py
```

### Step 2: Register in `~/.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

Restart Claude Code. The hook will activate on the next bash command.

## Log format

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-06-18T08:55:00] BLOCKED: SQL DROP statement
  command: DROP TABLE users;
  project: /home/user/my-project

[2026-06-18T08:56:12] BLOCKED: rm with -r and -f flags
  command: rm -rf node_modules
  project: /home/user/another-project
```

## Testing

You can pipe a fake Claude Code payload to the hook:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"},"cwd":"/tmp"}' \
  | python3 pre-tool-use-block-destructive.py
```

Expected output: a JSON object with `"decision": "block"`.

For a passing command:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' \
  | python3 pre-tool-use-block-destructive.py
```

Expected output: nothing (exit 0, no JSON).

## Customization

Edit `BLOCKED_PATTERNS` in `pre-tool-use-block-destructive.py` to add/remove patterns. The format is `(regex, human-readable-reason)`.

## License

MIT
