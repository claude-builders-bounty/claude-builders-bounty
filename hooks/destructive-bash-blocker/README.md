# destructive-bash-blocker

A Claude Code `pre-tool-use` hook (Python, stdlib-only) that intercepts dangerous bash commands before they run.

## What it blocks

| Pattern                                          | Why                                                              |
|---------------------------------------------------|------------------------------------------------------------------|
| `rm -rf /`, `rm -rf $HOME`, `rm -rf .`, `rm -fr ~/...` | Catastrophic, near-impossible to recover from                    |
| `DROP TABLE`                                     | Destroys table + data without migration trail                    |
| `git push --force` / `git push -f`               | Rewrites remote history, breaks teammates' clones                |
| `TRUNCATE [TABLE]`                               | Wipes table; ROW-level rollback unreliable across engines        |
| `DELETE FROM <table>` without `WHERE`            | Empties the table                                                |
| `mkfs.*`                                         | Formats a filesystem                                             |
| `dd if=... of=/dev/...`                          | Raw write to a device                                            |
| Fork bomb (`:(){ :\|:& };:`)                     | Saturates process table                                          |

Every block is logged to `~/.claude/hooks/blocked.log` as one JSON line per attempt (timestamp, command, pattern, reason, project path).

## Install (2 commands)

```sh
mkdir -p ~/.claude/hooks
curl -L https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/destructive-bash-blocker/hook.py -o ~/.claude/hooks/destructive-bash-blocker.py
```

Then register the hook in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python ~/.claude/hooks/destructive-bash-blocker.py" }]
      }
    ]
  }
}
```

(If you already have a `PreToolUse` array, append the entry to it.)

## How it works

Claude Code pipes a JSON event to the hook's stdin before every `Bash` tool call. The hook inspects `tool_input.command` and, if any rule matches, prints `{"decision":"block","reason":"..."}` on stdout — Claude refuses the call and shows the reason. Non-matching commands produce no output and pass through.

## Verifying the hook is wired

Try this in a Claude Code session:

```
> rm -rf /
```

Expected: a block message naming the pattern + a new line in `~/.claude/hooks/blocked.log`.

## Tuning

Edit the `RULES` list in `hook.py`. Each entry is `(re.Pattern, reason: str)`. Adding a rule:

```python
(re.compile(r"\bsudo\s+rm\b"), "sudo rm has no undo. Use git-trash or trash-cli."),
```

Patterns are deliberately conservative — a false positive that asks the user to retry in a real shell is cheaper than a true negative that nukes their `$HOME`.

## License

MIT, matches the parent repo.
