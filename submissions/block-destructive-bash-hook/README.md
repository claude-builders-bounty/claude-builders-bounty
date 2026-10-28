# Block destructive bash (Claude Code hook)

PreToolUse hook for [bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

Blocks these Bash patterns before they run:

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Normal commands (`ls`, `git status`, `rm file.txt`, `DELETE FROM … WHERE …`) are left alone.

Each block is appended to `~/.claude/hooks/blocked.log` as:

`timestamp<TAB>reason<TAB>project-path<TAB>command`

Claude sees a deny decision plus a short explanation on stderr (exit 2).

## Install (one command)

From this folder:

```bash
python3 install.py
```

That copies `block_destructive.py` to `~/.claude/hooks/` and registers a `PreToolUse` / `Bash` matcher in `~/.claude/settings.json`. Restart Claude Code.

## Test (optional)

```bash
python3 test_block_destructive.py
```
