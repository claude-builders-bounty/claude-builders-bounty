# Destructor Guard (PreToolUse hook)

A single-file Python hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks) that **blocks destructive bash commands before they run**: recursive delete of the filesystem root or home directory, force-pushes to `main`/`master`, `DROP TABLE`/`TRUNCATE`, `mkfs`, `dd` to raw disks, `chmod -R 777` on `/`, fork bombs, `shutdown`/`reboot` and friends.

Built for [claude-builders-bounty issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

## How it works

- Registered as a `PreToolUse` hook for the `Bash` tool in `~/.claude/settings.json`.
- Receives the standard hook JSON on stdin, inspects only `tool_input.command`.
- On a match: appends a JSON line to the log, prints a clear human-readable
  message on **stderr**, emits `{"decision":"block"}` on stdout and **exits 2**
  so Claude Code cancels the tool call.
- On no match (or non-bash input): exits 0 instantly. The hook itself is a
  ~150 line stdlib-only script - no dependencies, Python 3.7+.

## Install (two commands)

```bash
# 1) download the hook
curl -fsSL https://raw.githubusercontent.com/7777add7777-ai/claude-builders-bounty/hook-destructor-guard/hooks/destructor_guard.py -o ~/.claude/destructor_guard.py

# 2) register it (idempotent - safe to re-run)
python3 <(curl -fsSL https://raw.githubusercontent.com/7777add7777-ai/claude-builders-bounty/hook-destructor-guard/hooks/install_destructor_guard.py)
```

Verify: pipe a destructive sample into the hook and expect exit code `2` plus
the block message on stderr (see the test suite below for a ready-made sample).

## Blocked patterns

| Pattern | Example that gets blocked |
|---|---|
| recursive `rm` of `/`, `~`, `$HOME`, `/*` | `rm -rf /`, `rm -fr ~`, `rm --recursive --force /` |
| force push to `main`/`master` (incl. `--mirror`) | `git push --force origin main`, `git push -f origin master` |
| `DROP TABLE` / `DROP DATABASE` / `TRUNCATE` | `psql -c "DROP TABLE users"` |
| `mkfs*` | `mkfs.ext4 /dev/sda1` |
| `dd` with `of=/dev/<disk>` | `dd if=/dev/zero of=/dev/sda bs=1M` |
| redirect into a raw block device | `echo x > /dev/sda` |
| `chmod ... 777` on `/` or `~` | `chmod -R 777 /` |
| fork bomb | `:(){ :&#124;:& };:` |
| power actions | `sudo shutdown -h now`, `reboot` |

Safe operations are never touched: `rm -rf ./build`, `git push --force origin feature-x`, `git push origin main`, `chmod 644 file`, ...

## Logging

Every blocked attempt is appended to `~/.claude/destructor-guard.log` as a JSON
line: `{"ts": ..., "command": ..., "reason": ...}`. Override the path with the
`DESTRUCTOR_GUARD_LOG` environment variable.

## Uninstall

Remove the `destructor_guard` entry from `hooks.PreToolUse` in
`~/.claude/settings.json` and delete `~/.claude/destructor_guard.py`.

## Tests

`python3 tests/test_destructor_guard.py` runs 27 destructive/safe cases through
the hook and asserts the exit codes (blocked => 2, allowed => 0).
