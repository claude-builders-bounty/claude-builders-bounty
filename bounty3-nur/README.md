# block_destructive_commands — Claude Code PreToolUse hook

Blocks a curated set of destructive shell patterns *before* Claude Code
executes them: recursive force-remove (`rm -rf`), forced git pushes
(`git push --force` / `-f`), `DROP TABLE`, `TRUNCATE`, and
`DELETE FROM <table>` with no `WHERE` clause.

Solves [#3 — HOOK: Pre-tool-use hook that blocks destructive bash commands](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/
# then merge the "hooks" block from settings.example.json into ~/.claude/settings.json
```

## How it works

Claude Code calls the hook with a JSON payload on stdin before running any
`Bash` tool call. The hook:

- Allows everything by default (fails open on non-Bash tools, missing
  commands, or malformed JSON — it never crashes and never blocks
  something it can't parse).
- Matches the command against five destructive patterns.
- If a match is found:
  - prints the modern `hookSpecificOutput` / `permissionDecision: "deny"`
    JSON on stdout,
  - also exits with code `2` and writes a human-readable reason to
    stderr (for the classic exit-code hook contract),
  - appends a structured JSONL record to `~/.claude/hooks/blocked.log`
    with `timestamp`, `attempted_command`, `project_path`, and `reason`.
- Normal commands (including `rm file.txt`, `git push origin main`,
  `DELETE FROM t WHERE id=1`) pass through untouched.

## Design notes

- **Fails open, never fails loud.** A bug in this hook should never be
  the reason a legitimate command gets stuck — malformed input or
  unexpected payload shapes always allow (exit 0), they never crash.
- **Precise patterns, not blunt substring bans.** e.g. `DELETE FROM x`
  is only blocked when there's no `WHERE` anywhere in the statement;
  `rm -rf` is matched independent of flag order (`-rf` or `-fr`).
- **No third-party dependencies.** Pure Python 3 standard library —
  nothing to install, nothing that can silently break.

## Test

```bash
python3 tests/test_hook.py
```

18/18 checks pass: blocking behavior for each dangerous pattern, safe
commands passing through, non-Bash tools being ignored, malformed input
failing open, and the JSONL log format being well-formed.

## Disclosure

Implemented by Nūr (an AI agent) end-to-end: pattern design, hook I/O
contract (both the exit-code and the JSON `hookSpecificOutput` paths),
and the full test suite were written and run by the agent, not copied
from an existing PR on this issue.
