# Block Destructive Commands — Claude Code PreToolUse Hook

A [Claude Code](https://code.claude.com/docs/en/hooks) `PreToolUse` hook that intercepts dangerous bash commands before they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` / `rm -r -f` / `rm --recursive --force` | Recursive force delete (any flag order) |
| `DROP TABLE` / `DROP DATABASE` | SQL schema destruction |
| `git push --force` / `git push -f` / `git push +<ref>` / `git -c push.force=true push` | Rewrites remote history (allows `--force-with-lease` and `-c push.force=false`) |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM ...` (without `WHERE`) | Unconditional SQL row deletion |
| `dd ... of=/dev/*` | Raw disk overwrite |
| `> /dev/sd*` / `>> /dev/nvme*` | Shell redirect to raw block device |
| `mkfs` / `mkfs.ext4` | Filesystem format (destroys data) |
| `wipefs` | Disk signature wipe |
| `:(){ :|:& };:` fork bomb | Process exhaustion attack |

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh
```

The installer copies the hook to `~/.claude/hooks/` and merges the `PreToolUse` entry into `~/.claude/settings.json` without overwriting your other hooks.

Uses the official Claude Code `hookSpecificOutput` schema (`permissionDecision: deny`) — not the legacy `decision: block` format.

## How it works

1. Intercepts every `Bash` tool call via the `PreToolUse` hook
2. Checks the command against destructive patterns (including chained commands joined with `;`, `&&`, or `||`)
3. **Blocks** matching commands and returns a clear denial message to Claude
4. **Logs** every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
5. **Allows** safe commands to pass through unchanged

## Hook protocol

Claude Code sends JSON on stdin. When a command is blocked, the hook prints the official denial schema:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Recursive force delete (rm -rf) blocked. Run this command directly in your terminal if you truly need it."
  }
}
```

Safe commands produce no stdout and exit `0`.

## Blocked log

```bash
cat ~/.claude/hooks/blocked.log
```

Example entry:

```
[2026-06-06T12:34:56Z] Command: rm -rf /tmp/build | Project: /home/user/project
```

## Tests

From the repository root:

```bash
python3 -m unittest discover -s hooks/block-destructive-commands/tests -v
# 59 regression tests
```

## License

MIT
