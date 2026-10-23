# PreToolUse Hook — Block Destructive Commands

A Claude Code [PreToolUse hook](https://code.claude.com/docs/en/hooks) that blocks dangerous bash commands before they run.

## What it blocks

- `rm -rf` and equivalents: `rm -fr`, `rm -Rf`, `rm -r -f`, `rm -f -r`, `rm --recursive --force`, including `sudo rm -rf`
- SQL `DROP TABLE`
- SQL `TRUNCATE` / `TRUNCATE TABLE`
- SQL `DELETE FROM` **without** a `WHERE` clause
- `git push --force` / `git push -f` (`--force-with-lease` is intentionally allowed)
- `mkfs.*` filesystem creation and `dd of=/dev/...` block-device overwrites

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC timestamp, the attempted command, the project path, and the reason. The hook prints a `permissionDecision: deny` JSON response, so Claude sees exactly why the command was refused. Everything else — including parsing failures or a missing JSON interpreter — exits 0 untouched and never interferes with normal bash commands.

## Install (one command)

```bash
curl -fsSL https://raw.githubusercontent.com/1132dadf/claude-builders-bounty/1132dadf-patch-1/hooks/install.sh | bash
```

This downloads the hook to `~/.claude/hooks/pre-tool-use.sh` and registers it for Bash in `~/.claude/settings.json`. Restart Claude Code afterwards.

Manual install (two commands):

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/1132dadf/claude-builders-bounty/1132dadf-patch-1/hooks/pre-tool-use.sh -o ~/.claude/hooks/pre-tool-use.sh
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

Then add the registration snippet from `install.sh` to `~/.claude/settings.json`.

## Test

```bash
bash hooks/test_pre_tool_use.sh
```

The suite covers all blocked patterns, flag permutations, the `--force-with-lease` exemption, `DELETE FROM ... WHERE`, malformed payloads, and verifies that blocked attempts are logged. It does not require network access.

```bash
echo '{"tool_input":{"command":"rm -rf /"}}' | ~/.claude/hooks/pre-tool-use.sh
# -> permissionDecision: deny + blocked.log entry

echo '{"tool_input":{"command":"ls -la"}}' | ~/.claude/hooks/pre-tool-use.sh
# -> exit 0 (allowed)
```

## Requirements

`bash` and any one of `python3`, `python`, or `jq` for reading the hook payload. If none is available the hook fails open rather than blocking every command.
