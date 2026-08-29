# Sample review

- Source PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2271
- Diff truncated: no
- Generated with: Claude Code `pr-reviewer` agent

---

## Summary
This PR adds a self-contained Claude Code `PreToolUse` hook (`block_destructive_bash.sh`), a Node-based `settings.json` installer, a README, and a bash regression test that block a set of destructive Bash patterns (`rm -rf`, force push, SQL `DROP/TRUNCATE/DELETE FROM` without `WHERE`, `git reset --hard`, block-device writes, `curl|bash`). The overall structure is reasonable and the installer's preserve-and-backup behavior is a nice touch. However, the hook fails open on several common error paths, depends on bash 4.4+ / Node without checking, and the regex-only matching has both bypasses and false positives that matter for a security control.

## Identified Risks
- **[High] Fails open on parse/runtime errors (`block_destructive_bash.sh`).** If `node` is missing, JSON parsing fails (`process.exitCode = 2`), or the payload shape is unexpected, `parsed_fields` ends up empty, `command` is empty, and the script `exit 0`s — silently allowing the command. A security hook should fail closed (deny) when it cannot inspect the input.
- **[High] `mapfile -d ''` requires bash ≥ 4.4.** The installed hook is invoked as `bash ~/.claude/hooks/block_destructive_bash.sh`; on macOS the default `/bin/bash` is 3.2, where `mapfile` does not exist. Combined with the fail-open behavior above, the hook would silently allow every command on default macOS shells. No version check or fallback (e.g., `read -r -d ''` loop, or doing all extraction in Node) is present.
- **[Medium] `WHERE` detection is a substring match.** `[[ ! "$lower_command" =~ where ]]` matches any occurrence of `where` anywhere in the command, so `psql -c "DELETE FROM users"; echo somewhere` or a table/column named `*where*` bypasses the "DELETE FROM without WHERE" rule.
- **[Medium] Trivially bypassable command matching.** Patterns anchor on `(^|[[:space:];&|])rm`, so `/bin/rm -rf /`, `$(which rm) -rf /`, `sudo -- /bin/rm -rf /`, `find . -delete`, or `rm -rf` built via variables/`eval` are not caught. Command substitution and backtick contexts are also not considered. This is inherent to regex matching but should be documented as best-effort rather than "cannot bypass" (the README's claim about bypass resistance only covers JSON escaping, not shell obfuscation).
- **[Medium] Log lines can be invalid JSON.** `json_escape` only escapes `\` and `"`; tabs, `\r`, and other control characters are emitted raw (invalid per JSON spec), and `tr -d '\n'` concatenates multi-line commands with no separator, corrupting the recorded command. Any downstream log parser will choke or misread the attempted command.
- **[Medium] False positives that will block legitimate work.**
  - `git[[:space:]]+push([^;&|])*-f($|[[:space:]])` matches a branch/ref whose name ends in `-f` (e.g. `git push origin feature-f`).
  - `sql_execution_context` is command-wide, so `mysql -e "SELECT 1" && truncate -s 0 log.txt` is blocked as a "TRUNCATE statement", and `psql --help | grep "drop table"` is blocked as `DROP TABLE`.
  - `remote script execution` triggers on any command containing `curl`/`wget`, a `|`, and the substring `bash`/` sh`/`|sh` anywhere — e.g. `curl -s api.example.com | jq . > bash_notes.txt` or `wget -q url && cat run.sh | head`.
- **[Low] Privacy: full command text is persisted.** `~/.claude/hooks/blocked.log` records complete commands, which frequently contain tokens, passwords, or connection strings, and is created with the default umask (typically world-readable). No rotation or size bound either.
- **[Low] Installer edge cases (`install_settings.sh`).** Each run overwrites `settings.json.bak` (a second run destroys the pre-install backup); a `settings.json` that fails `JSON.parse` aborts with a raw Node stack trace after the hook file has already been copied; `node` availability is never checked; and rewriting via `JSON.stringify` discards any comments/formatting a user had.
- **[Low] `command=` shadows the `command` builtin** in the hook script; harmless today but a foot-gun if the script later calls `command -v`.
- **[Low] Test coverage gaps.** No tests for: missing/failing `node`, malformed JSON payload, absent `tool_input.command`, multi-line command logging, `/bin/rm -rf`, or `WHERE`-substring bypass. `expect_allowed` asserts only that no log file exists — it does not assert stdout is empty, so a deny emitted without logging would pass.

## Improvement Suggestions
- Make the hook fail closed: if Node is unavailable, exits non-zero, or produces fewer than three fields, emit a `deny` (or at minimum `ask`) payload plus a stderr diagnostic instead of `exit 0`. Explicitly distinguish "no Bash command present" (safe allow) from "could not parse" (deny).
- Remove the bash 4.4 dependency — either do the entire extraction and matching in Node (single process, no `mapfile`, and proper JSON escaping for free), or replace `mapfile -d ''` with a portable `while IFS= read -r -d '' field; do ...` loop and add an explicit `BASH_VERSINFO` guard.
- Tighten the `WHERE` check to a word/clause-scoped match on the same statement segment (e.g. require `delete[[:space:]]+from[^;]*[[:space:];(]where([[:space:]]|$)`), rather than a bare substring over the whole command line.
- Fix `json_escape` to handle control characters, or generate the log line with `node -e 'process.stdout.write(JSON.stringify({...}))'` / `jq -n` so escaping is correct by construction; keep newlines as `\n` rather than deleting them.
- Narrow the false-positive-prone rules: require `-f` to be a standalone argument for `git push` (`(^|[[:space:]])-f($|[[:space:]])` evaluated on the push segment only), scope SQL checks to the command segment containing the SQL runner, and require the pipe target to actually be a shell (`\|[[:space:]]*(sudo[[:space:]]+)?(ba|z|da)?sh([[:space:]]|$)`) for the remote-script rule.
- `chmod 600` the log file on creation and document/bound its growth; consider redacting obvious secret patterns or logging a hash/prefix instead of the full command.
- In the installer: only create `settings.json.bak` if it does not already exist (or use a timestamped backup), wrap `JSON.parse` in a try/catch with a clear error message that instructs the user to fix or move the file, and check `command -v node` up front before copying anything.
- Rename the `command` variable to `bash_command`, and add regression tests for the fail-closed paths, malformed JSON, `/bin/rm -rf`, the `WHERE`-substring case, and multi-line command logging; have `expect_allowed` also assert empty stdout and exit status 0.
- Soften the README's claim that "escaped quotes, backslashes, and command newlines cannot bypass inspection" to describe JSON-level parsing only, and state plainly that shell-level obfuscation can defeat the pattern matching.

## Confidence: High
