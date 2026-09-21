# Pre-tool-use hook: block destructive bash commands

A Claude Code **PreToolUse** hook that inspects every Bash command before
execution and blocks the ones that can do irreversible damage (deleting
root, force-pushing, `DROP TABLE`, writing to a block device, formatting a
filesystem, ...). Blocked attempts are logged for audit.

## Install (1 command)

```bash
bash destructive-hook/install.sh
```

That's it. The installer copies the hook to `~/.claude/hooks/` and
registers it under `PreToolUse` in `~/.claude/settings.json` (existing
settings are preserved).

## How it works

- `scripts/destructive_hook.py` reads the PreToolUse JSON payload from
  stdin, extracts the shell command, runs it through 17 regex rules, and
  exits with code **2** (deny) plus an explanation on stderr when a
  destructive pattern matches. The model sees the reason and can adjust
  its approach.
- Every blocked attempt is appended to **`~/.claude/hooks/blocked.log`**:
  timestamp, why it was blocked, the project path (the `cwd` from the
  hook payload), and the attempted command.
- `testcases/` holds 30 allowed/blocked cases plus a runner that also
  verifies the log line format.

## Test

```bash
python3 destructive-hook/testcases/run_tests.py
```

All destructive cases must be blocked (exit 2), all safe cases must pass
(exit 0), and the log check verifies `blocked.log` lines contain the
timestamp, reason, project path, and command.

## Detected patterns

| Pattern | Why blocked |
|---|---|
| `rm -rf /` / `rm -rf ~` / `sudo rm -rf` | recursive force delete of a broad path |
| `git push --force` / `git push -f` / `git push +refspec` | overwrites shared history |
| `git reset --hard` | discards working-tree changes |
| `git clean -fdx` | deletes untracked files |
| `DROP TABLE/DATABASE/SCHEMA/INDEX` | irreversible SQL |
| `TRUNCATE` | drops all rows |
| `DELETE FROM x` without `WHERE` | wipes the table |
| `> /dev/sd*` / `> /dev/nvme*` | raw write to a block device |
| `mkfs` / `mkfs.ext4` | formats a filesystem |
| `dd ... of=/dev/...` | writes a block device |
| `chmod -R 777 /` | world-writable on root |
| `kill -9 1/2/3/4` | kills init / critical daemons |
| `shred` / `wipefs` | secure-deletes / wipes signatures |

**Not blocked** (intentionally): `git push --force-with-lease` (safe
force push), `DELETE ... WHERE ...` (scoped delete), `rm -rf ./build` /
`rm -rf dist` (scoped cleanups), and normal development commands.

## Extending

Add a `(pattern, reason)` tuple to `DESTRUCTIVE_RULES` in
`scripts/destructive_hook.py`. Keep the regex specific enough that
normal development commands still pass.

To log to a different file, set `DESTRUCTIVE_HOOK_LOG` in the hook
environment before the command.
