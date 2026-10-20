# 🛡 Claude Code Pre-Tool-Use Security Hook

Intercepts and blocks destructive bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, unbounded `DELETE`) before they are executed. Logs every incident to `~/.claude/hooks/blocked.log`.

## ⚡ Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

---

## 🔒 Blocked Patterns
- Recursive forced file deletions (`rm -rf`, `rm -fr`)
- Database structural wipes (`DROP TABLE`, `DROP DATABASE`, `TRUNCATE`)
- Unbounded deletions (`DELETE FROM table` without `WHERE`)
- Destructive git rewrites (`git push --force`, `git push -f`)
- Block device and partition formatters (`mkfs`, `dd if=`)
- Fork bombs and denial of service triggers

All violations are immediately aborted with code `1` and appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and working directory. Safe developer commands (`git status`, `npm test`, `rm single_file.txt`) are permitted without latency.
