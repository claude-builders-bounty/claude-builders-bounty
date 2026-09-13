# Claude PreToolUse Hook — Block Destructive Bash ($100 bounty #3)

Claude Code `PreToolUse` hook that intercepts dangerous bash commands **before**
they execute. Exit `2` blocks (message shown to Claude), exit `0` allows.

Blocked: `rm -rf`/`rm -fr` · `DROP TABLE` · `TRUNCATE` ·
`git push --force`/`-f` (safe `--force-with-lease` still allowed) ·
`DELETE FROM` without `WHERE`. Read-only mentions (`grep DROP TABLE ...`,
`echo ...`) are allowed; commented lines (`# rm -rf /`) are allowed.

Every block is appended to `~/.claude/hooks/blocked.log`:

```text
2026-09-12T21:55:00+00:00 | cwd=/proj/demo | rule=rm-rf | command=rm -rf /
```

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-guard/block_destructive_bash.py ~/.claude/hooks/
cp hooks/destructive-guard/settings.example.json ~/.claude/settings.json
```

Or if you cloned the template `.claude/` folder directly:

```bash
cp -r .claude ~/.claude && python3 ~/.claude/hooks/block_destructive_bash.py < /dev/null && echo hook-ok
```

## Verify

```bash
python3 test_hook.py
# ALL PASS (10 must-block + 11 must-allow + e2e log check)
echo '{"tool_input":{"command":"rm -rf /"},"cwd":"/proj/demo"}' \
  | python3 block_destructive_bash.py; echo "exit=$?"
# BLOCKED [rm-rf]: ... exit=2
```

## Sample run (real repo: this bounty workspace)

```text
[OK] should BLOCK: rm -rf / -> rm-rf
[OK] should BLOCK: psql -c 'DROP TABLE users;' -> drop-table
[OK] should BLOCK: git push --force origin main -> git-force-push
[OK] should BLOCK: psql -c 'DELETE FROM users' -> delete-without-where
[OK] should ALLOW: git push --force-with-lease origin main -> None
[OK] should ALLOW: psql -c 'DELETE FROM users WHERE id = 1' -> None
ALL PASS
```
