# claude-hook-guard

Claude Code `PreToolUse` hook that blocks destructive bash commands before they run. Python stdlib only, no dependencies. Works on **Windows (PowerShell), Linux, and macOS**.

## What it blocks / allows

| Command | Verdict | Why |
|---|---|---|
| `rm -rf /`, `rm -rf ./build`, `rm -r`, `rm -R`, `rm --recursive`, `sudo rm -rf …`, `/bin/rm -rf …`, `"rm" -rf …` | ⛔ BLOCK | Any recursive `rm` is blocked regardless of target (conservative: even `./build` — delete specific files with plain `rm`, or run it yourself; absolute-path and quoted forms included) |
| `DROP TABLE …` (any case) | ⛔ BLOCK | Irreversible table wipe |
| `git push --force`, `git push -f`, `git push origin +main`, `git push origin +refs/heads/main` | ⛔ BLOCK | Rewrites shared history (`+<refspec>` forces without any flag) |
| `git push --force-with-lease`, `--force-if-includes` | ✅ ALLOW | Documented choice: these are the safe force-push variants |
| `TRUNCATE …` (any case) | ⛔ BLOCK | Instantly wipes all rows |
| `DELETE FROM t` (no `WHERE`) | ⛔ BLOCK | Would delete every row |
| `DELETE FROM t WHERE …` (any case) | ✅ ALLOW | Restrictive `WHERE` present |
| `ls`, `git status`, `git push`, `npm test`, `rm file.txt`, `echo …` | ✅ ALLOW | Normal commands pass through silently |

Chained payloads (`;`, `&&`, `||`, `|`, newlines) are inspected per segment, so `echo hi; rm -rf /` still blocks. SQL matching is case-insensitive. Multi-statement input is split on `;`, so `DELETE … WHERE …; DELETE FROM logs` blocks on the second statement.

## Known limitations

Plain-text guardrail, not a sandbox — it matches the command string as written and does not decode or expand obfuscation.

| Input | Handling | Why |
|---|---|---|
| `sh -c "rm -rf /"`, `bash -c "…"`, `cmd /c …` | ⚠️ Best-effort | Matched as plain text only (simple forms are caught); variable expansion, string concatenation, or encoded payloads inside wrappers are not unpacked |
| SQL `/* … */` comments (`DROP/**/TABLE`) | ➖ Not blocked | Keyword patterns require plain whitespace |
| Missing whitespace (`DELETE FROMusers`) | ➖ Not blocked | SQL patterns require `\s+`; as written this is not valid SQL |
| Backslash escapes (`r\m -rf`) | ➖ Not blocked | Shell escaping is not normalized |
| Python APIs (`shutil.rmtree(…)`, `os.remove(…)`) | ➖ Out of scope | Only the Bash command string is inspected |

## Install (2 commands)

**Linux / macOS (bash):**

```bash
mkdir -p ~/.claude/hooks && cp hook.py ~/.claude/hooks/hook.py
cp settings.example.json ~/.claude/settings.json  # or merge the "hooks" block into your existing settings
```

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path ~/.claude/hooks; Copy-Item hook.py ~/.claude/hooks/hook.py
# then merge settings.example.json ("hooks" block) into ~/.claude/settings.json (create it if missing)
```

> Windows note: the example uses `python ~/.claude/hooks/hook.py`. If `python` isn't on your PATH, use `py` or `python3` in the `command` field instead. On Linux/macOS make the hook executable: `chmod +x ~/.claude/hooks/hook.py`.

Verify the wiring with a dry run (expects `BLOCK … exit 2`):

```bash
python ~/.claude/hooks/hook.py --check "rm -rf /"; echo "exit=$?"
```

## How it works

1. Claude Code sends the `PreToolUse` event JSON on stdin (`tool_input.command`, `cwd`).
2. `hook.py` checks the command against the 5 rules above.
3. **Blocked:** writes a `deny` decision as JSON to stdout **and** a plain-language reason to stderr, exits `2` (universal block signal — either channel alone blocks on every client version). Appends one line to `~/.claude/hooks/blocked.log` with timestamp, rule, project path, and command.
4. **Allowed:** exits `0` with no output, so the normal permission flow continues untouched. Empty/malformed input also exits `0` — the hook never breaks unrelated tools.

`blocked.log` line format:

```
[2026-09-07T10:15:01+00:00] BLOCKED rule=rm_recursive cwd=/home/dev/my-project command=rm -rf /
```

Override the log location with `CLAUDE_HOOK_BLOCKED_LOG` (used by the tests so they never touch your real log).

## Test

```bash
python -m pytest -v        # full suite (recommended)
python hook.py --test      # built-in self-tests, no pytest needed
```

## Files

| File | Purpose |
|---|---|
| `hook.py` | The hook (stdlib only). Also supports `--check "<cmd>"` and `--test` |
| `settings.example.json` | Drop-in `PreToolUse` → `Bash` matcher config for `~/.claude/settings.json` |
| `test_hook.py` | pytest suite: all 5 patterns blocked, normals allowed, edge cases, stdin→exit-code→log end-to-end |
| `blocked.log.sample` | Example of `~/.claude/hooks/blocked.log` entries |
| `README.md` | This file |

No network calls, no secrets, no dependencies.
