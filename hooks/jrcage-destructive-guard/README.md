# Destructive Bash guard for Claude Code

Submission for [bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3). Python 3.10+ standard library; no network or dependencies. AI-assisted implementation by Codex for JRCage.

## Install in two commands

Run from a reviewed checkout of this PR:

```sh
python3 -m unittest discover -s hooks/jrcage-destructive-guard -v
python3 hooks/jrcage-destructive-guard/install.py
```

The installer copies the hook under `~/.claude/hooks/`, merges a Bash `PreToolUse` matcher into `~/.claude/settings.json`, preserves other settings/hooks, and saves the initial settings as `settings.before-jrcage-guard.json`. Repeating installation with the same Python executable adds no duplicate matcher. Restart Claude Code and inspect `/hooks` to verify the Bash hook is active. Windows requires a POSIX-compatible Claude Code shell; native PowerShell is outside this submission.

## Behavior

- Denies literal `rm` commands combining recursive and force options, including separate/reordered options and common wrappers.
- Denies `git push --force`, `-f`, force-with-lease and explicit `+` refspecs.
- Denies `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without a top-level `WHERE` in that SQL statement. Inspects inline arguments to sqlite3, psql, mysql, mariadb, duckdb and sqlcmd. SQL literals/comments do not supply a WHERE; a later statement's WHERE cannot excuse an earlier delete.
- Inspects command lists, pipelines and literal nested `sh -c`/`bash -c` strings. Never executes the inspected command.
- Writes one JSON line per blocked Bash attempt to `~/.claude/hooks/blocked.log`: UTC timestamp, original command, project path (`cwd`), reason. New logs are mode 0600. Newlines are escaped to preserve one-record-per-line parsing. A log-write failure still denies the command and explains the missing audit record.
- Returns the documented `hookSpecificOutput` PreToolUse `permissionDecision: deny` and a reason Claude can see. Ordinary commands emit nothing and exit zero, leaving Claude Code's normal permission flow intact. Other tools are unaffected. Malformed/oversized input is denied explicitly.

The log contains full attempted commands, which can contain secrets. Keep it local; redact before sharing. Existing log permissions are not changed. Removal: delete the installed hook's Bash matcher from settings (keep other matchers), then delete `~/.claude/hooks/jrcage-destructive-guard.py`. The backup is a reference, not an instruction to overwrite newer settings.

## Scope and validation limits

This is a literal-command guardrail, **not a sandbox or a full Bash/SQL parser**. It cannot resolve aliases/functions, variable expansion, generated/eval code, encoded programs, SQL loaded from files/stdin, all SQL dialects, or substitutions embedded inside quoted arguments. SQL inspection is conservative and can reject unusual but harmless SQL; a WHERE clause is not proof that deletion is safe. Keep Claude Code permission controls and least-privilege database credentials enabled. Do not treat this hook as a boundary against an adversarial agent.

Tests run the actual hook protocol and installer with disposable homes, plus command decision fixtures. Destructive commands appear only as strings and never run. No authenticated Claude Code session or native Windows session was available: protocol compatibility is checked against the [official hook reference](https://code.claude.com/docs/en/hooks), and interactive end-to-end validation remains for the maintainer. No other contributors' implementations were used.
