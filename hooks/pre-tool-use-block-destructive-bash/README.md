# Claude pre-tool-use destructive command blocker

Install:
```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_blocker.py ~/.claude/hooks/pre_tool_use_blocker.py
chmod +x ~/.claude/hooks/pre_tool_use_blocker.py
```
Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`. Blocked attempts append JSONL to `~/.claude/hooks/blocked.log`.
