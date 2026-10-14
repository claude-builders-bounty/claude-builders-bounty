# BUILD NOTES — verification against the live hooks docs, and design decisions

## Verified against the official docs (fetched 2026-10-08)

Source: **https://docs.anthropic.com/en/docs/claude-code/hooks** ("Hooks
reference — Claude Code Docs"), read in full for the sections below before
writing any code. Key facts the implementation relies on, in my own words:

* **Delivery**: command hooks receive the event payload as JSON on stdin.
  `PreToolUse` fires after tool parameters are created and before the call
  executes, and it is one of the events that can block.
* **Input shape**: besides the common fields (which include `cwd`,
  `session_id`, `hook_event_name`, `permission_mode`), `PreToolUse` carries
  `tool_name`, `tool_input`, and `tool_use_id`. For the Bash tool,
  `tool_input.command` holds the shell command string. The hook reads exactly
  those fields.
* **Blocking mechanism (chosen)**: exit 0 while printing a JSON object whose
  `hookSpecificOutput` contains `permissionDecision: "deny"` and a
  `permissionDecisionReason`. The docs present this JSON route as the
  finer-grained alternative to exit code 2, and state that for `"deny"` the
  reason is shown to Claude — which is what the bounty criterion "a clear
  message to Claude explaining what was blocked and why" asks for. The
  payload I emit is limited to the fields the docs list for `PreToolUse`
  (`hookEventName`, `permissionDecision`, `permissionDecisionReason`) so it
  passes their schema validation; an invalid object on exit 0 would be
  treated as a non-blocking error, so I deliberately add nothing else (no
  `systemMessage`, no extra keys).
* **Exit-code semantics**: 0 = success (stdout treated as JSON only when it
  starts with `{` and ends with `}` — my safe path therefore prints nothing
  at all, and non-JSON noise can never be misread); 2 = blocking error whose
  message comes from stderr when no JSON decision is present. I use the JSON
  deny instead of exit 2 because it carries a structured reason; several
  hooks' decisions resolve with `deny` taking precedence anyway.
* **Matcher**: on `PreToolUse`, `matcher` filters by tool name, so `"Bash"`
  scopes the hook to Bash calls exactly as the bounty requires. (The docs
  note a `Bash|PowerShell` matcher covers the PowerShell tool on Windows; my
  hook also accepts `tool_name: "PowerShell"` input defensively, but the
  shipped install wires only `Bash`, per the criteria.)
* **Config shape**: settings files nest event → matcher group → handlers;
  user-level config lives in `~/.claude/settings.json`. `install.py` merges
  into that structure rather than overwriting it.
* **Why hooks belong in `~/.claude/hooks/`**: the criteria specify that
  directory for both the script and `blocked.log`; the docs' own walkthrough
  uses a hooks directory with an executable script, which matches.

One bug the docs-first pass did *not* save me from, found by testing:
`shlex.split()` silently rejects the `punctuation_chars` keyword (it's a
constructor parameter of the `shlex` class). First test run: 28 passed /
69 failed because the exception was being swallowed by the fail-open guard.
Fixed by driving the `shlex.shlex` class with `whitespace_split = True`;
final run is 97/97. Lesson recorded here because it's the kind of thing a
reviewer re-running the tests will see in the git history of the corpora:
fail-open is the right default for a hook, but it makes "hook crashed" and
"command allowed" indistinguishable without a corpus that asserts on the
deny JSON — which is why `run_tests.py` parses the stdout JSON instead of
trusting exit codes.

## Design decisions

1. **`--force-with-lease` is blocked** (as are `--force-if-includes` and the
   `+refspec` spelling). Force-with-lease is safer than `--force` — it
   refuses to overwrite commits you haven't seen — but it still rewrites
   published history, and the accident this hook exists to prevent (an agent
   pushing with stale assumptions) is stopped by the lease check failing,
   not by allowing the flag. Failing closed costs one manual push; failing
   open can cost a team's shared branch. Teams that want it can delete one
   string from `FORCE_PUSH_FLAGS` in `block_destructive.py`; the README says
   where.
2. **`rm -r <dir>` without `-f` is allowed.** Recursive deletion of a single
   named directory (`node_modules`, `build/`) is routine; the dangerous
   delta is `-f` (no prompts, no undo), `--no-preserve-root`, or aiming
   recursion at `/`, `~`, `$HOME`, `.`, `..`, or a glob. Those all block.
3. **SQL checks are context-scoped.** SQL patterns are only evaluated when a
   known database client is executing somewhere in the pipeline, or when raw
   SQL was pasted as the command itself. That's what lets
   `grep -rn "DROP TABLE" .` and `echo 'Never run DROP TABLE in prod'` pass
   while `echo 'TRUNCATE TABLE logs' | mysql mydb` and heredocs into a
   client still block. Trade-off accepted: a command line that both mentions
   destructive SQL innocuously *and* runs an unrelated client call can
   false-positive (rare, and fails in the safe direction).
4. **`DELETE FROM` is evaluated per statement**: the text after each
   `DELETE FROM` up to the next `;`/newline must contain a `WHERE`. A mixed
   string (`DELETE FROM a; DELETE FROM b WHERE id=1`) blocks on the first
   statement; a `WHERE` in a later statement can't launder an earlier one.
5. **Extra coverage beyond the minimum**: `DROP DATABASE` / `DROP SCHEMA`
   are blocked alongside `DROP TABLE`, and `git push` bundled short flags
   (`-fu`) count as force. All listed in the README pattern table.
6. **Fail-open on hook errors, fail-closed on matches.** Unparseable stdin,
   unbalanced quotes (which bash would also reject), or any unexpected
   exception exits 0 silently — a buggy hook must never wedge a session.
   Conversely, once a rule matches, the deny is issued even if writing
   `blocked.log` fails.
7. **Token-based, not substring-based.** The command is lexed with the
   stdlib `shlex` class (`punctuation_chars="|&;"`), so quoted text stays a
   single token: that's the whole reason `echo "rm -rf is dangerous"` passes
   and `git commit -m "remove -rf flag handling"` passes, while the same
   words in command position block. Wrappers (`sudo`, `env`, `VAR=1`,
   `xargs`, `stdbuf`, …) are skipped when locating the real program, and
   `/bin/rm` counts as `rm`.
8. **Known evasions (documented, accepted)**: `eval`, variable-constructed
   commands (`$RM -rf`), base64/`$(...)`-assembled strings, SQL built by an
   interpreter (`python -c` with a DB driver), and docker-wrapped clients
   are out of scope. This is an accident guardrail, not a sandbox; the
   README says so plainly.
9. **Log format**: `[ISO-8601-timestamp] cwd=<cwd> rule="<rule>" command=<one-line command>`.
   ISO timestamps sort lexicographically; one physical line per attempt
   keeps the log greppable. The `BLOCK_DESTRUCTIVE_LOG` env override exists
   solely so the test-suite can redirect the log to a temp file — default is
   the required `~/.claude/hooks/blocked.log`.

## How the deliverable maps to the acceptance criteria

| Criterion | Where it's met |
| --- | --- |
| Official hooks format, `~/.claude/hooks/`, `PreToolUse` + Bash matcher, stdin JSON, documented block mechanism | `install.sh`/`install.py`, `settings.snippet.json`, `block_destructive.py` (deny via `hookSpecificOutput.permissionDecision`) |
| Blocks `rm -rf` + variants, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` w/o WHERE | `check_rm` / `check_git` / `check_sql`; 34-case dangerous corpus, all blocking |
| Log every block with timestamp + command + project path | `log_block()` → `~/.claude/hooks/blocked.log`; test-suite asserts one exact entry per dangerous case |
| Clear message to Claude on block | `permissionDecisionReason` text (shown to Claude per the docs) |
| No interference with normal commands | Token-based matching; 25-case safe corpus incl. all required near-misses, asserting empty stdout |
| Python 3 stdlib only, settings snippet, ≤2-command install | `block_destructive.py` imports only stdlib; `settings.snippet.json`; README install = clone + `./install.sh` (verified end-to-end in a sandbox HOME) |
| Real tests, run, saved output | `tests/run_tests.py`, `tests/results.txt` → **97 passed, 0 failed** |
