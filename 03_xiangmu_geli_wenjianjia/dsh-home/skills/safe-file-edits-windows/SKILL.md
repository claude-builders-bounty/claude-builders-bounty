---
name: safe-file-edits-windows
description: Recover refused writes and fuzzy-patch corruption.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [file-editing, patch, write-file, indentation, windows, recovery]
    related_skills: [unattended-agent-execution, evidence-backed-deliverables, edit-config-files-wsl]
---

# Safe File Edits (Windows / Hermes)

`write_file` guards against stale or partial reads, and `patch` falls back to fuzzy matching when `old_string` is not an exact match. Both guards are correct, but chained they deadlock: the rewrite is refused, so you patch, `patch` "succeeds" with a shifted edit boundary, and the Python file stops compiling. This skill is the decision tree that breaks that loop and the repair procedure that actually restores the file.

## When to Use

- `write_file` returns `Refusing to overwrite <f>: … was modified since you last read it on disk`
- `write_file` returns `… was last read with offset/limit pagination (partial view). Read the remaining pages, or use patch, before overwriting it`
- `patch` returns `"success": true` **plus** `"note": "Non-exact match (strategy: block_anchor …)"` or `context_aware`
- `patch` result carries `"lint": {"status": "error", "output": "IndentationError…"}`, or the next run raises `IndentationError` / `SyntaxError`
- bash refuses an inline python edit: `unexpected EOF while looking for matching '` or `SyntaxError: unterminated string literal`

Don't use for: creating new files (plain `write_file`), or editing Hermes `config.yaml` (that is `edit-config-files-wsl`).

## Prerequisites

- The target file exists and you know its absolute path
- Either the file is git-tracked with only your edits dirty, or you take a `.bak` copy before the rewrite

## How to Run

```bash
# After every edit to a .py file — the only proof that counts
terminal(command="cd <repo> && python -m py_compile src/<file>.py", timeout=120)
```

Silent = compiles. Any `IndentationError` / `SyntaxError` means the edit is not done, whatever the tool reported.

## Quick Reference

| Symptom | What it means | Action |
|---|---|---|
| `was modified since you last read` | Another writer (worker, service, your own script) touched it | `read_file` again, then edit |
| `last read with offset/limit pagination` | Guard needs a **complete** read of the current file | `read_file` with no `offset`/`limit`, then `write_file` |
| `note: Non-exact match (strategy: …)` | Edit landed on an approximate span — boundaries may have shifted | Immediately read the region **and** `py_compile`; treat as broken until proven |
| `lint.status: error` on a successful patch | Patch already corrupted indentation | Revert the hunk, re-anchor, or restore from git |
| `unexpected EOF while looking for matching` | bash ate your quotes (heredoc or nested `python -c`) | Write a `.py` with `write_file`, run `python <file>` |
| `unterminated string literal` at `line 1` | Same cause: the shell truncated `\"import …` | Same fix — never inline multi-line Python |

## Procedure

1. **Classify the refusal by its exact text.** Three different guards, three different fixes; the message names the guard. Completion: you can quote which of the Quick Reference rows you hit.
2. **Clear a partial-view refusal with a complete read.** Call `read_file(path)` with no `offset`/`limit` (page with `offset` until `next_offset` is absent, for files over ~100K chars), then call `write_file` with the whole merged content. Completion: `write_file` returns `verified: true`.
   **When the file is zero bytes this fix cannot work** — there are no pages left to read, and the guard still reports the pagination message. Do not loop on `read_file`. Escape instead: `write_file` the content to a scratch path, then `cp <scratch> "<target>"` in `terminal`, and verify with `ls -l` + `head -3` + `tail -3`. This is the only route that reliably clears the guard on an empty target.
3. **Never accept a fuzzy patch as done.** On `Non-exact match`, immediately `read_file` the edited span ±20 lines and run `python -m py_compile`. Completion: compile exit 0 **and** the region shows no duplicated line.
4. **Repair by reverting the hunk, not by patching again.** In order of preference: `git checkout -- <file>` when the file's only dirty change is this edit; restore your `.bak`; **a sibling copy** — a delivery/dist package holding the same file, or a `*.bak_<tag>` next to it, is often a byte-identical earlier snapshot and is the fastest restore when the file is untracked and you took no backup; or a second `patch` whose `old_string` is the exact corrupted block just read. Never re-issue the same `old_string`/`new_string` — the same fuzzy strategy re-corrupts it. Completion: `py_compile` exit 0 and `git diff -- <file>` shows only the intended hunk.
5. **Anchor correctly the next time.** `old_string` must start and end on complete lines, include the leading whitespace of every line, and carry 1–2 unique neighbouring lines. Any anchor line that appears twice in the file (repeated guard clauses are the classic) is disqualified — that is how a body gets duplicated. Completion: `grep -c "<anchor line>" <file>` returns 1.
6. **For replacements over ~40 lines, stop patching.** Full read → edit in memory → `write_file`, then `py_compile`. Completion: same as step 2.
7. **When the shell is the only route left, use a script file.** `write_file` a `repair_<topic>.py` into the repo or scratch dir, run `terminal(command="python repair_<topic>.py")`, then delete or commit it deliberately. Completion: script exits 0 and the target passes `py_compile`.

## Pitfalls

- **Two `IndentationError`s on the same span = stop patching, switch to a line-based script.** CRLF endings are the usual tell: the visible text matches, the fuzzy matcher re-indents the surrounding lines, and every retry corrupts a different block. Do not try a third anchor — jump to step 7.
- **For pure insertions, prefer a line-scanning inserter over `patch`.** Read `readlines()`, emit the anchor line unchanged, then append the new block with an explicit indent prefix, and `writelines()`. Untouched lines are never re-emitted, so indentation cannot shift — unlike any `old_string`/`new_string` round-trip.
- **`patch` returning `success: true` is not evidence of a correct edit.** Read `note` and `lint` in the same result. A `success: true` + `lint.status: error` payload is a corrupted file that the tool reported as a success.
- **`block_anchor` / `context_aware` can duplicate a line.** Observed in `cs_orchestrator.py`: a fuzzy patch pushed a `if not any(intent in consult_intents …)` guard into the block twice (lines 182 and 184) and mis-indented the `if should_handoff:` that followed, so the file failed at line 180 on the next import.
- **Do not answer a refusal with a shell rewrite.** Of the refusals followed by another tool call, the largest group hit a *second* error in `terminal` (quote mangling, `unexpected EOF`) rather than a fix; only the full-`read_file` route reliably cleared the guard.
- **`write_file` also refuses after a partial read, even when the file has not changed.** Reading 2000 of 2600 lines does not count as having read the file — page to the end or read the whole file at once.
- **A zero-byte target is a dead end for the read-first fix.** `read_file` returns `total_lines: 0, file_size: 0`, yet the next `write_file` is still refused with the same pagination text — there is nothing left to read, so no amount of re-reading satisfies the guard. Write to scratch and `cp` it over. Repeating `read_file` here burns turns and never converges.
- **`I/O operation on closed pipe` in piped output is benign.** It is asyncio teardown noise from the child process, not the failure you were looking for; fix the real error and it disappears.
- **`execute_code` is unavailable in cron/worker runs.** Do not build the repair around it — see `unattended-agent-execution`.

## Verification

```bash
cd <repo>
python -m py_compile <file>                  # exit 0, no output
git diff --stat -- <file>                    # only the intended file
git diff -- <file> | grep -c '^+[^+]'        # added-line count matches the plan
sed -n '<a>,<b>p' <file> | sed 's/^[[:space:]]*//' | sort | uniq -d   # empty = no duplicated line
```

Done means: compiles, diff is the intended hunk only, no duplicated line in the edited region. A rewritten file that compiles but contains the same guard twice is still a broken edit.

---

*Distilled 2026-10-19 from a 7-day window of 29 Hermes sessions / 9,670 messages. Witnessed frequencies: `write_file` partial-view refusals 180 messages across 13 sessions; `Non-exact match` patch results 26 (22 in one file-edit session); patch `success:true` + `lint.status:error` 29 messages across 2 sessions; `IndentationError`/`SyntaxError` 183 messages across 5 sessions; bash quoting failures (`unexpected EOF`, `unterminated string literal`) 64 messages across 5 sessions.*
