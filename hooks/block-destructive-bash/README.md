# Block destructive bash commands

A Claude Code [`PreToolUse` hook](https://code.claude.com/docs/en/hooks) that stops
destructive shell commands before they run, tells Claude why, and records every
blocked attempt in `~/.claude/hooks/blocked.log`.

Python 3.7+, standard library only. No `jq`, no pip install.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-bash/block_destructive_bash.py -o ~/.claude/hooks/block_destructive_bash.py
python3 ~/.claude/hooks/block_destructive_bash.py --install
```

`--install` adds the hook to `~/.claude/settings.json`, keeping any hooks already
configured there and backing the file up to `settings.json.bak` first. It is
idempotent, so running it twice does nothing the second time. Restart Claude Code
(or run `/hooks`) to load the hook, and `/hooks` again to confirm it appears
under `PreToolUse`.

Working from a clone instead? Copy the file and run the same second command:

```bash
cp hooks/block-destructive-bash/block_destructive_bash.py ~/.claude/hooks/
python3 ~/.claude/hooks/block_destructive_bash.py --install
```

To configure it by hand instead, merge [`settings.example.json`](settings.example.json)
into `~/.claude/settings.json`.

## What gets blocked

| Rule | Blocked | Allowed |
|---|---|---|
| `rm-rf` | `rm -rf /tmp/x`, `rm -fr`, `rm -r -f`, `rm --recursive --force`, `sudo rm -rf /` | `rm file.txt`, `rm -r build`, `rm -f stale.lock` |
| `git-force-push` | `git push --force`, `git push -f origin main`, `git push origin +main:main` | `git push`, `git push --force-with-lease` |
| `sql-drop-table` | `psql -c "DROP TABLE users"` | `grep -rn "DROP TABLE" migrations/` |
| `sql-truncate` | `mysql -e "TRUNCATE logs"`, `truncate -s 0 app.log` | `npm run truncate-logs` |
| `sql-delete-without-where` | `psql -c "DELETE FROM users"` | `psql -c "DELETE FROM users WHERE id=1"` |

`git push --force-with-lease` is allowed on purpose: it aborts instead of
discarding commits the local clone has not fetched, so it is the alternative the
hook points Claude toward. Set `BLOCK_FORCE_WITH_LEASE = True` at the top of the
script to block it too.

## Not tripping over safe commands

The hook tokenizes the command the way a shell does rather than grepping the raw
string, so quoting and command structure are respected:

- `echo "rm -rf /"` and `grep -rn "DROP TABLE" migrations/` are allowed — the
  dangerous text is an argument to a program that only prints or reads.
- `bash -c "rm -rf /tmp/x"`, `find . | xargs rm -rf`, and `cd /tmp && rm -rf build`
  are blocked — nested shells, pipelines, and `&&` chains are each inspected.
- Commands the tokenizer cannot parse (unbalanced quotes, for example) fall back
  to pattern matching, so a malformed command cannot slip a rule past the hook.

Anything that matches no rule produces no output at all. The hook deliberately
does not answer `"allow"`, because that would suppress the permission prompt
Claude Code would otherwise show you; staying silent lets your normal permission
settings decide.

## What Claude sees when a command is blocked

```
Blocked by the destructive-command hook (rule: rm-rf).

Command: rm -rf /var/data
Why: `rm -rf` deletes whole directory trees with no prompt and no undo.
Instead: Delete specific paths without `-rf`, or ask the user to run it themselves
if the recursive delete is really intended.

This attempt was logged to ~/.claude/hooks/blocked.log. Do not retry the same
command; if the user explicitly wants it, ask them to run it themselves.
```

You also get a one-line warning in the terminal via `systemMessage`.

## The log

One JSON object per line in `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-09-13T16:34:43Z", "rule": "rm-rf", "command": "rm -rf /var/data", "project_path": "/home/dev/api", "session_id": "abc123"}
```

`timestamp` is UTC ISO-8601, `project_path` is `$CLAUDE_PROJECT_DIR` when set and
otherwise the session's working directory. JSON lines keep multi-line commands on
a single record, so the log stays greppable:

```bash
tail -n 20 ~/.claude/hooks/blocked.log | jq -r '"\(.timestamp) \(.rule) \(.project_path) — \(.command)"'
```

## Check a command without running it

```bash
python3 ~/.claude/hooks/block_destructive_bash.py --check 'git push --force'
```

Prints the verdict and exits 1 when the command would be blocked, 0 when it
would be allowed. Nothing is logged.

## Tests

```bash
python3 hooks/block-destructive-bash/test_hook.py
```

54 checks: every allow and block case in the table above, plus the log file
contents, non-Bash and malformed input handling, and `--install` / `--uninstall`
against a throwaway `HOME`. The suite runs the hook as a subprocess with real
`PreToolUse` payloads on stdin, so it exercises the same path Claude Code uses.

## Uninstall

```bash
python3 ~/.claude/hooks/block_destructive_bash.py --uninstall
```

Removes only this hook's entry from `~/.claude/settings.json` and leaves your
other hooks alone.

## Limits worth knowing

- Pattern matching is not a sandbox. It covers the patterns above and common
  spellings of them, not every possible way to destroy data (`dd`, `> file`,
  `find -delete`, `DROP DATABASE`). Add rules to `RULES` and a matching `check_*`
  function as your team needs them.
- The hook only sees commands Claude Code runs. Your own shell is untouched, so
  running a blocked command yourself is the intended escape hatch.
- A hook denial is deterministic and overrides `bypassPermissions` mode.

MIT licensed, same as the rest of this repo.
