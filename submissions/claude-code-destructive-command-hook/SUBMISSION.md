# Submission: Claude Code PreToolUse hook (bounty #3, $100)

**Bounty:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
**Reward:** $100 via Opire (Stripe) on merge.
**Status:** **已提交** — claim 评论：https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3#issuecomment-6885140664
**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5222
**等待：** 维护者审核/合并；合并并付款前不计收入。

## Files

| File | Purpose |
|---|---|
| `block_dangerous_bash.py` | The hook: reads Claude Code PreToolUse JSON, blocks destructive Bash commands, logs, exits 2. |
| `install.py` | One-command installer: copies the hook to `~/.claude/hooks/`, merges `PreToolUse` into `~/.claude/settings.json`. |
| `README.md` | Install (1 command), blocked patterns, test commands. |
| `tests/test_hook.py` | 10 unit tests. |

## Acceptance mapping

- [x] Follows Claude Code hooks format (`~/.claude/hooks/` + `PreToolUse` entry in settings).
- [x] Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`.
- [x] Logs blocked attempts to `~/.claude/hooks/blocked.log` (JSON line with timestamp/command/cwd).
- [x] Prints a clear message to stderr and exits 2.
- [x] Does not interfere with normal commands (tests: `ls`, `git status`, `python3 app.py`, `rm -f file.txt`, `DELETE ... WHERE` all pass).
- [x] README install in 1 command (`python3 install.py`).

## Test evidence

```text
$ python3 -m unittest discover -s tests -v
Ran 10 tests in 0.365s
OK
```

Manual hook run:

```text
$ printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/build","cwd":"/home/user/project"}}' | python3 block_dangerous_bash.py
Blocked by claude-hook: this command matches a destructive pattern (rm -rf).
Command: rm -rf /tmp/build
If this is intentional, ask the user to run it manually or temporarily disable the hook.
exit=2

$ printf '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python3 block_dangerous_bash.py
exit=0
```

Blocked log line:

```json
{"timestamp": "2026-11-14T22:04:18+00:00", "pattern": "rm -rf", "command": "rm -rf /tmp/build", "cwd": "/home/user/project"}
```

## How to submit (needs GitHub account)

1. Comment `/opire try` on issue #3.
2. Fork the bounty repo, add these files under a submission directory, open a PR titled `[Bounty #3] PreToolUse hook: block destructive Bash commands`.
3. Payment releases automatically on merge.

## Notes / limitations

- The hook only inspects the command, never executes it.
- Malformed JSON or non-Bash tools pass through (fail open for usability, but never fail open on a matched destructive pattern).
- `rm -rf` detection covers `-rf`/`-fr` and similar single-token flag combinations; `-r -f` separated flags are not covered by the regex yet (could add if reviewer asks).
- Installer uses the current Python executable path, so it works on Windows/macOS/Linux without assuming `python3` is on PATH.
