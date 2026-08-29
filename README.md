# Claude Code Pre-Tool Hook: Destructive Command Blocker

A lightweight security hook that intercepts dangerous bash commands before execution in Claude Code sessions.

### Blocked Operations
- `rm -rf` / `rm -fr` / `rm -r -f` (recursive forced deletions)
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` / `git push -f`
- `DELETE FROM` statements without a `WHERE` clause

### Quick Setup

```bash
mkdir -p ~/.claude/hooks
cp block_destructive_commands.py ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

### Running Tests

```bash
python3 test_hook.py
```
