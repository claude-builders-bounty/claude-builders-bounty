# block-destructive-bash — Claude Code pre-tool-use hook

Intercepts **Bash** commands before Claude Code runs them and blocks destructive
patterns, logging every attempt.

## Install (2 commands)
```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/
```
```bash
# merge the "hooks" block into ~/.claude/settings.json
cat settings.example.json
```

## Blocked patterns
`rm -rf` / `rm -fr` · `DROP TABLE` · `TRUNCATE TABLE` · `DELETE FROM` without `WHERE`
· `git push --force` / `-f` (allows `--force-with-lease`) · `mkfs` · `dd of=/dev/...`
· fork bomb · `chmod -R 777`. Benign commands pass untouched.

## Behavior
- Exit **0** → allow. Exit **2** → block; the reason is shown to Claude.
- Every block is appended to `~/.claude/hooks/blocked.log`:
  `<ISO timestamp>\t<reason>\t<command>\t<project path>`
- Malformed hook payloads never break the session (fail open, exit 0).

## Test
```bash
python3 tests/test_hook.py     # 7 tests, stdlib only
```

## Uninstall
Remove the `PreToolUse` entry from `~/.claude/settings.json` and delete
`~/.claude/hooks/block_destructive.py`.
