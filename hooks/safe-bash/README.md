# safe-bash

A Claude Code **pre-tool-use** hook that intercepts dangerous shell commands before they execute. Patterns matched:

- `rm -rf` (and every flag-ordering: `-fr`, `-Rf`, `-rfv`, `-r -f`, `--recursive --force`)
- `DROP TABLE` (case-insensitive)
- `git push --force` / `git push -f` / `git push origin +ref`
- `TRUNCATE TABLE` (case-insensitive)
- `DELETE FROM <table>` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, pattern name, project path, and the full command.

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/hooks/safe-bash/install.sh
```

The installer copies the hook into `~/.claude/hooks/safe-bash/` and either creates `~/.claude/settings.json` (if missing) or prints the JSON snippet you need to merge.

If you prefer to wire it up manually, add this to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "$HOME/.claude/hooks/safe-bash/pre_tool_use.py" }
        ]
      }
    ]
  }
}
```

## What Claude sees when a command is blocked

When the hook blocks a tool call, Claude receives this structured response on stdout:

```json
{
  "decision": "block",
  "reason": "Destructive command blocked by safe-bash hook: 'rm -rf'. Use `rm -ri` for interactive removal, or remove specific paths explicitly. If you really mean to recursively force-delete, ask the user to run the command themselves. (logged to /home/you/.claude/hooks/blocked.log)"
}
```

For older Claude Code versions that read the hook output from stderr + exit code, the same reason is also written to stderr and the script exits with code 2 — the documented "block" exit code.

## What gets logged

Tab-separated, one line per blocked attempt:

```
2026-05-20T02:21:42+00:00	rm -rf	/home/you/projects/api	rm -rf /tmp/build
2026-05-20T02:22:08+00:00	git push --force	/home/you/projects/api	git push -f origin main
2026-05-20T02:23:51+00:00	DELETE FROM ... (no WHERE clause)	/home/you/projects/api	psql -c 'DELETE FROM users'
```

## Test it

```bash
bash hooks/safe-bash/test.sh
```

The harness ships 28 fixtures (15 block cases, 11 allow cases, 2 edge cases). At commit time **all 28 pass**:

```
== BLOCK cases (expect exit 2) ==
  PASS  [rm -rf /]
  PASS  [rm -rf path]
  PASS  [rm -fr]
  PASS  [rm -rfv]
  PASS  [rm -Rf]
  PASS  [rm -r -f]
  PASS  [rm --recursive --force]
  PASS  [DROP TABLE]
  PASS  [drop table (lowercase)]
  PASS  [TRUNCATE TABLE]
  PASS  [DELETE FROM no WHERE]
  PASS  [delete from (lowercase)]
  PASS  [git push --force]
  PASS  [git push -f]
  PASS  [git push +ref]

== ALLOW cases (expect exit 0) ==
  PASS  [rm single file]
  PASS  [rm -i]
  PASS  [rm -r alone]
  PASS  [rm -f alone]
  PASS  [DELETE with WHERE]
  PASS  [SELECT]
  PASS  [git push normal]
  PASS  [git push --force-with-lease]
  PASS  [ls]
  PASS  [rfm typo (not rm)]
  PASS  [git rm a file]

== Edge cases ==
  PASS  [non-Bash tool payload allowed]
  PASS  [empty stdin allowed]

================================
  PASS: 28
  FAIL: 0
================================
```

## Design notes

- **Substring matching, not shell tokenization.** A command like `echo 'rm -rf safe'` will be blocked because the hook does not parse shell quoting. This is intentional: conservative-by-default is safer than missing a real `rm -rf` hidden behind heredocs, `bash -c`, or `eval`. If you have a legitimate need to pass a destructive pattern as data, run that command outside Claude.
- **Per-statement `DELETE` analysis.** SQL is split on `;` so each `DELETE FROM` statement is checked independently — `DELETE FROM logs WHERE id=1; DELETE FROM users` will block on the second statement even though the first one is safe.
- **`--force-with-lease` is allowed.** It's the safe form of force-push (rejects if the remote has moved). Only bare `--force` / `-f` / refspec `+ref` are blocked.
- **`-R` is treated as `-r`.** GNU `rm` accepts both as recursive.
- **Tool-name agnostic to schema version.** The hook reads `tool_name`/`tool`/`tool_input`/`input`/top-level `command` so it works with both old and new Claude Code event payloads.

## File layout

```
hooks/safe-bash/
├── pre_tool_use.py    # the hook (Python 3, no deps)
├── settings.json      # example PreToolUse config to merge into ~/.claude/settings.json
├── install.sh         # 2-command installer
├── test.sh            # 28-case test harness
└── README.md          # this file
```

## Uninstall

```bash
rm -rf ~/.claude/hooks/safe-bash
```

Then remove the `PreToolUse > Bash` block from `~/.claude/settings.json`.
