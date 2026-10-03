# Claude Code Pre-Tool-Use Safety Hook

Intercepts and blocks destructive terminal and database commands before execution in Claude Code.

## Protected Patterns
- Recursive force removals (`rm -rf`, `rm -fr`, `rm -r -f`)
- Unrestricted table drops (`DROP TABLE`)
- Forced git branch overwrites (`git push --force`, `git push -f`)
- Full table purges (`TRUNCATE TABLE`)
- Unrestricted SQL deletions (`DELETE FROM` without `WHERE`)

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_safety_hook.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use_safety_hook.py
```

## Audit Logging
Blocked attempts are automatically recorded to `~/.claude/hooks/blocked.log` with timestamp, reason, project path, and attempted command.

## Running Tests
```bash
python3 test_safety_hook.py
```
