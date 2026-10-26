## What
`block-dangerous.sh` — a zero-dependency Claude Code **PreToolUse** hook that blocks destructive bash commands (`rm -rf`, force pushes, `dd`, `chmod 777`, etc.) before execution, with logging and a clear reason message aimed at Claude.

## Files
- `hook/block-dangerous.sh` — the hook (pure bash, no dependencies beyond coreutils)
- `hook/README.md` — what it does + 2-step installation
- `hook/settings.example.json` — ready-to-merge `settings.json` snippet
- `hook/test.sh` — self-test: pipes sample PreToolUse JSON payloads through the hook and asserts block/allow per case

## Verification
- All test cases pass (dangerous payloads blocked, safe payloads allowed), run against a temp HOME so no real `~/.claude` is touched
- Every blocked command is appended to `~/.claude/hooks/blocked.log` with timestamp, command, and cwd
- Output includes the modern hook JSON (`decision: "block"`) plus the legacy `decision`/`reason` form for older clients

## Acceptance criteria mapping
- Follows the Claude Code PreToolUse hook format ✓
- Blocks destructive commands and never interferes with normal ones ✓
- Logs to `~/.claude/hooks/blocked.log` ✓
- Prints a clear reason message to Claude ✓
- Installation in ≤ 2 commands ✓
