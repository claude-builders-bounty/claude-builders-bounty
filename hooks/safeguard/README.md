# Safeguard Hook (Claude Code PreToolUse)

Blocks destructive bash commands before Claude Code executes them.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/safeguard/safeguard.py ~/.claude/hooks/safeguard.py && chmod +x ~/.claude/hooks/safeguard.py
```

Then register (settings snippet):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/safeguard.py" }]
      }
    ]
  }
}
```

## Blocked patterns (acceptance)

| Pattern | Example |
|---------|---------|
| recursive/force rm | `rm -rf /tmp/foo` |
| force push | `git push --force`, `git push -f` |
| hard reset / clean -f | `git reset --hard`, `git clean -fd` |
| SQL DROP / TRUNCATE | `DROP TABLE users`, `TRUNCATE TABLE logs` |
| DELETE without WHERE | `DELETE FROM logs` |
| mkfs / dd to device | `mkfs.ext4`, `dd of=/dev/sda` |
| power commands | `shutdown`, `reboot` |
| curl/wget pipe to shell | `curl … | bash` |
| fork bomb / chmod -R 777 / crontab -r | … |

Safe commands (e.g. `ls`, `git status`, `npm test`, `DELETE … WHERE …`) are allowed.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/safeguard-blocked.log`:

```
2026-09-14T03:00:00Z	recursive/force rm	/path	rm -rf build
```

Fields: UTC timestamp, reason, project path (cwd), attempted command.

## Model feedback

Hook exits with code `2` and writes a clear stderr message so Claude Code blocks the tool and the model sees why.

## Tests

```bash
python3 test_safeguard.py
```

8/8 passing (allow safe, block rm -rf / force-push / DROP / DELETE-no-WHERE / curl|bash; allow DELETE with WHERE).
