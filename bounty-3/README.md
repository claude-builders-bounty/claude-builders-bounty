# Destructive-command PreToolUse guard

This contribution implements bounty #3 with a shareable Claude Code `PreToolUse`
hook. It reads the tool-call JSON from stdin and denies only the destructive
patterns required by the bounty:

- recursive forced deletion (`rm -rf`, including equivalent combined flags)
- `DROP TABLE`
- `git push --force` / `--force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not contain a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with the UTC
timestamp, attempted command, project path, and reason. Safe commands emit no
decision, so Claude Code's normal permission flow continues unchanged.

## Install

From this repository checkout, install the committed project hook into another
Claude Code project in two commands or fewer. Replace `/path/to/project` with
the target project directory:

```bash
mkdir -p /path/to/project/.claude/hooks && cp .claude/hooks/destructive_command_guard.py /path/to/project/.claude/hooks/
cp .claude/settings.json /path/to/project/.claude/settings.json
```

If the target already has a `.claude/settings.json`, merge the `PreToolUse`
entry instead of overwriting unrelated project settings.

For this repository itself, the hook and settings are already committed at the
correct project-local paths, so no install step is required after checkout.

## Verify

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests exercise each required blocked pattern, safe near-misses, structured
denial output, and append-only audit logging without executing any destructive
command.
