# Claude Code destructive-command guard

A best-effort PreToolUse guard for Bash commands. Python 3.9+ required.

## Install (one command)
```bash
python3 .claude/hooks/install-block-destructive.py
```
The installer uses the current Python interpreter, copies the guard into ~/.claude/hooks/, validates existing settings before writing, preserves unrelated hooks/permissions, and saves the original settings once as settings.json.before-destructive-guard.bak. Repeating the same installation does not add the same command twice. Restart Claude Code to load the configuration. Windows usage requires the Bash environment used by Claude Code and a callable Python executable.

## Behavior
- Blocks recursive forced rm with combined, separated, or long flags.
- Blocks DROP TABLE, TRUNCATE and DELETE FROM lacking WHERE outside SQL comments/literals.
- Blocks forced git push, including force-with-lease, short force flags and forced refspecs.
- Harmless echo/grep text is not treated as a command; shell separators and common shell -c wrappers are inspected.
- Every successfully logged denial is a JSON line in ~/.claude/hooks/blocked.log with UTC timestamp, original command, project_path and reason. New log files are created with restrictive permissions where supported.
- A logging failure still denies the command and reports a diagnostic. Invalid hook input denies rather than silently allowing.
- Safe commands emit no decision; normal Claude Code permissions remain in force.

## Verification
```bash
python3 -m unittest discover -s .claude/hooks -p test_block_destructive.py -v
```
Eight tests passed, including dangerous-command variants, ten safe examples, JSON denial, log-call arguments, failure-to-log behavior, malformed input, and installer settings preservation/idempotency. Tests never execute the dangerous command strings. External CLI and real Claude hook installation were not exercised; log writes are mocked in unit tests.

## Limits
This is not a shell or SQL security sandbox. Arbitrary scripts, aliases, variable expansion, dynamic eval, uncommon wrappers, heredocs and all SQL dialects are not comprehensively interpreted. It may conservatively block ambiguous commands. Keep Claude Code's normal permissions and OS/database controls enabled. Do not treat this denylist as protection against arbitrary hostile code.
The log contains original commands and may include sensitive text. Keep it private and rotate/archive it according to your local retention policy.

## Scope cleanup
The unrelated Family Guard application and workflow were removed from this bounty branch only. The prior state remains in commit 17fca49bdc99d1e30de4dbb3b730950895cf2115 and archive/bounty-3-before-scope-cleanup-20260929.
