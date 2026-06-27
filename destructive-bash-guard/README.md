# Destructive Bash Guard (Claude Code PreToolUse Hook)

Blocks dangerous bash commands before Claude Code executes them:

- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Install (2 commands)

**Step 1:** Copy the hook into Claude Code's hooks directory.

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block_destructive_bash.py ~/.claude/hooks/
```

**Step 2:** Merge the hook into your user settings (creates `~/.claude/settings.json` if missing).

```bash
python3 install.py
```

On Windows PowerShell, run `python install.py` from this folder instead.

## Validation

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Hook behavior

- Runs on `PreToolUse` for the `Bash` tool only.
- Safe commands pass through with no decision (normal permission flow).
- Blocked commands return `permissionDecision: deny` with a clear reason for Claude.
- Does not modify or intercept non-bash tools.

## Acceptance criteria (bounty #3)

- [x] Claude Code `PreToolUse` hook format
- [x] Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`
- [x] Logs to `~/.claude/hooks/blocked.log` (timestamp, command, project path)
- [x] Clear deny message to Claude
- [x] Safe commands unaffected
- [x] README install in 2 commands

Closes claude-builders-bounty/claude-builders-bounty#3
