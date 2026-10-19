# Destructive Bash guard

Python 3 standard-library PreToolUse hook for Claude Code. Install from this repository in one command:

```bash
python3 submissions/katarina-hook/install.py
```

Restart Claude Code. The installer merges the Bash hook into `~/.claude/settings.json`, preserves other settings and hooks, backs up existing settings, and installs under `~/.claude/hooks/`. Reinstalling does not duplicate the hook.

Blocks recursive forced `rm` (combined, split and long options), `git push --force`/`-f`, `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without a WHERE in the same SQL statement. SQL comments and quoted WHERE literals do not satisfy the condition. Recognizes `bash -c` wrappers. Denials use the documented `hookSpecificOutput.permissionDecision` format; ordinary commands emit no allow decision and retain Claude's normal permission checks.

Blocked attempts append JSON lines containing UTC timestamp, original command, project path and reason to `~/.claude/hooks/blocked.log`. Logging failures still deny the command and explain the failure. Invalid input is denied.

Validation: `python3 -m unittest discover -s submissions/katarina-hook -v` (5 tests, 20 command cases plus protocol/log/error checks).

Scope: this is a conservative guard, not a shell sandbox or complete SQL parser. It can reject literal SQL examples; aliases, dynamically assembled commands, arbitrary scripts and indirect SQL execution can bypass static inspection. It does not execute the inspected command. `--force-with-lease` retains normal permissions. Logs contain command text and should be treated as private.

Reference: https://code.claude.com/docs/en/hooks#pretooluse-decision-control

Uninstall: remove only the entry referencing `katarina_pre_tool_use.py` from settings, then remove that script. Keep other hooks.
