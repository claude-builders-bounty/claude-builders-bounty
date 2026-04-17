# Pre-tool-use Hook Configuration

This project includes a security hook that blocks destructive bash commands.

## Hook Installation

```bash
cp pre-tool-use-hook/hook.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Register the Hook

Add to your `~/.claude/CLAUDE.md` or project `.claude/CLAUDE.md`:
```
hook = "pre-tool-use"
```

## What the Hook Does

- Intercepts all `Bash` tool calls before execution
- Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE TABLE`, `DELETE FROM` without WHERE
- Logs blocked attempts to `~/.claude/hooks/blocked.log`
- Allows safe commands to proceed normally