# Block Destructive Commands — Claude Code PreToolUse Hook

A [Claude Code](https://code.claude.com/docs/en/hooks) `PreToolUse` hook that intercepts dangerous bash commands before they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` / `rm -r -f` / `rm --recursive --force` | Recursive force delete (any flag order) |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | SQL schema destruction |
| `git reset --hard` | Discards uncommitted and untracked local changes |
| `git push --force` / `git push -f` / `git push +<ref>` / `git -c push.force=true push` | Rewrites remote history (allows `--force-with-lease` and `-c push.force=false`) |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM ...` (without `WHERE`) | Unconditional SQL row deletion |
| `dd ... of=/dev/*` | Raw disk overwrite |
| `> /dev/sd*` / `>> /dev/nvme*` | Shell redirect to raw block device |
| `mkfs` / `mkfs.ext4` | Filesystem format (destroys data) |
| `wipefs` | Disk signature wipe |
| `:(){ :|:& };:` fork bomb | Process exhaustion attack |
| `curl ... \| bash` / `wget ... \| sh` | Remote script execution |

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh
```

The installer copies the hook to `~/.claude/hooks/` and merges the `PreToolUse` entry into `~/.claude/settings.json` without overwriting your other hooks.

To remove the hook:

```bash
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh --uninstall
```

Uses the official Claude Code `hookSpecificOutput` schema (`permissionDecision: deny`) — not the legacy `decision: block` format.

## How it works

1. Intercepts every `Bash` tool call via the `PreToolUse` hook
2. Splits chained commands on `;`, `&&`, and `||`, then checks each segment independently
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

From this directory:

```bash
make test
# or: python3 -m unittest discover -s tests -v
# 91 regression tests (bounty + peer-review acceptance + integration checks)
```

From the repository root:

```bash
npm test
# or: make ci-validate
# or: make -C hooks/block-destructive-commands test
```

The CI runner executes all regression tests, peer-review acceptance checks, and
attribution guards used by GitHub Actions.

## License

MIT
