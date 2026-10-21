# Destructive Bash command guard

A Python standard-library `PreToolUse` hook for bounty #3. It checks Bash tool
input before execution, explains denied commands to Claude, and records blocked
attempts as JSON lines. It never executes the command it inspects.

## Install

Requires Python 3.10+ and Git on macOS or Linux. From a directory where you keep
source checkouts, run these two commands:

```sh
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python3 claude-builders-bounty/hooks/destructive-command-guard/install.py
```

The installer copies the hook to `~/.claude/hooks/destructive-command-guard.py`
and registers a `PreToolUse` matcher for `Bash` in `~/.claude/settings.json`.
It preserves existing settings and handlers; repeating the same install does
not add duplicate registrations. A settings backup is saved on the first
change as `settings.json.before-destructive-guard`. Malformed settings and
symbolic-link targets are rejected rather than overwritten.

Restart Claude Code or reload the configuration through `/hooks`. For an
isolated configuration, pass `--config-dir /absolute/path/to/test-config` to
the installer; its installed command also uses that directory for logs. Tests
always pass explicit temporary directories and do not install into your profile.

## Behavior

The hook returns the documented `hookSpecificOutput` JSON with
`hookEventName: PreToolUse`, `permissionDecision: deny`, and a clear
`permissionDecisionReason` when a requested pattern is detected. Allowed
commands produce no decision, preserving Claude Code's normal permission flow.
Other tool names and hook events are ignored.

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with UTC timestamp,
the original command, the **event's project directory** (`cwd`), and the reason.
Each JSON line escapes embedded newlines. The hook continues to deny a blocked
command when logging fails and includes the logging error in its explanation.
The log contains command text, so apply the same access controls as your shell
history. The hook does not contact a network service.

The intended policy covers recursive forced `rm`, forced `git push`, SQL
`DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` in that statement.
Quoted text arguments to `echo`, `printf`, `grep`, and `rg`, and complete quoted
heredocs for standalone `cat`/`tee` commands, are treated as data. SQL string
literals and comments do not supply a `WHERE` clause. The safer
`git push --force-with-lease` is left to normal permission controls.

This is a guard against the listed accidental operations, not a Bash sandbox
or a complete SQL parser. It does not execute expansions, inspect aliases,
read script/SQL files, or interpret arbitrary programs such as `bash -c`.
Complex or multiple heredocs are conservatively inspected as text; they may
need manual review. Continue to use normal
Claude permissions, reviews, backups, and database access controls.

## Verify locally

From the repository root:

```sh
python3 -m unittest discover -s hooks/destructive-command-guard/tests -v
```

Tests feed command strings to real hook subprocesses as JSON. No destructive
command, SQL client, or Git push is executed. Installation tests use fresh
directories inside the test folder, check that existing settings survive,
and execute the registered hook command with synthetic events. This verifies
the local protocol and installer; it does not claim a live Claude conversation
was run.

The event and decision formats follow the
[official Claude Code hooks reference](https://code.claude.com/docs/en/hooks).

## Remove

Remove the handler pointing to `destructive-command-guard.py` from
`hooks.PreToolUse` in your settings, preserving other handlers. Then remove
that script if desired. Keep or delete `blocked.log` according to your needs.
The backup is a reference copy; restoring the whole backup could discard other
settings changes made after installation.
