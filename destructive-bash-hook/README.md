# Claude Code Destructive Bash Command Guard

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

Built for bounty issue: [#3 — HOOK: Pre-tool-use hook that blocks destructive bash commands](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

When a dangerous command is detected, the hook exits with code `2`, prints a clear explanation for Claude, and logs the attempt to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes:

- UTC timestamp
- project path
- block reason
- attempted command

## Install in 2 commands

```bash
chmod +x install.sh
./install.sh
```

The installer copies the hook to `~/.claude/hooks/destructive_command_guard.py` and adds this `PreToolUse` hook entry to `~/.claude/settings.json` if it is not already present:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/destructive_command_guard.py"
          }
        ]
      }
    ]
  }
}
```

The actual stored command is expanded to your home directory path for reliability.

## Manual install

```bash
mkdir -p ~/.claude/hooks
cp destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py
chmod +x ~/.claude/hooks/destructive_command_guard.py
```

Then add the `PreToolUse` settings entry shown above.

## How it works

Claude Code hook payloads are read from stdin. The script also supports `CLAUDE_TOOL_INPUT` as a fallback so it works with environment-variable-based hook setups.

The hook only gates Bash tool calls. Non-Bash tools are ignored silently.

Allowed commands exit `0` with no output, so normal Bash commands are not interrupted.

Blocked commands exit `2`, which Claude Code treats as a blocking hook result.

## Local testing

Run the test suite:

```bash
python3 -m unittest discover -s tests -v
```

Manual examples:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"echo safe"}}' | python3 destructive_command_guard.py
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"}}' | python3 destructive_command_guard.py
```

Expected result:

- `echo safe` exits `0`
- `rm -rf /tmp/demo` exits `2`, prints a block message, and appends to `~/.claude/hooks/blocked.log`

## Design notes

- The guard intentionally catches high-risk patterns only, not every possible dangerous command.
- The SQL `DELETE FROM` rule blocks statements without a `WHERE` before the statement terminator/end of input.
- `git push --force-with-lease` is also blocked because it still rewrites remote history.
- The script sanitizes newlines in log entries so each blocked attempt remains one log line.
