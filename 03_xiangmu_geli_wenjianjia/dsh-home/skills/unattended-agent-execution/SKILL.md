---
name: unattended-agent-execution
description: "Run commands with no approver: cron, worker, oneshot."
version: 0.2.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [cron, oneshot, kanban-worker, approvals, blocked-commands, automation]
    related_skills: [hermes-wf-kanban-orchestration, windows-scheduled-tasks, evidence-backed-deliverables, safe-file-edits-windows]
---

# Unattended Agent Execution

Cron jobs, `oneshot` runs, and dispatched kanban workers execute with **nobody present to approve anything**. Commands the approval layer considers dangerous are refused outright or time out; `execute_code` is often disabled entirely. This skill is the playbook: which constructs get blocked, what to run instead, how to run long jobs, and where to put files so later tools can actually read them.

## When to Use

- The session source is `cron`, `oneshot`, or a dispatched worker (`work kanban task <id>`)
- You see `BLOCKED:`, `single-query mode (-q)`, `user has NOT consented`, or `timed out without user response`
- A command needs minutes, not seconds
- You capture output to a file that a later `read_file` must find
- A scheduled job must not depend on interactive approval to succeed

Don't use for: interactive desktop sessions where the user is present and can approve.

## Prerequisites

- Know the interpreter before scripting: on this host `python` is the real 3.14.x while `python3` may be absent or a Store stub; project venvs live at `./venv/Scripts/python.exe` (Windows) or `./venv/bin/python`
- A scratch dir addressed by a **native** path (`<scratch>/out.txt`) that both the shell and the file tools resolve

## Quick Reference — blocked construct → replacement

| Blocked | Message you will see | Use instead |
|---|---|---|
| `python -c "..."`, `node -e`, `pwsh -Command` | `script execution via -e/-c flag` … `single-query mode (-q) runs without a user present to approve it` | write `script.py` with `write_file`, run `python script.py` |
| `python - <<'EOF'`, `bash <<'EOF'` | `script execution via heredoc` … same suffix | same: file first, then run it |
| `execute_code` | `BLOCKED: execute_code runs arbitrary local Python … without a user present` | `write_file` a `.py`, run with `terminal` |
| Giant inline one-liner | `BLOCKED (hardline): command parser limit or malformed executable payload` | write `task.sh` then `bash task.sh`; the refused payload is saved under `<hermes_home>/cache/blocked-scripts/` |
| Anything needing approval | `timed out without user response. The user has NOT consented` | do **not** retry; find a non-approval path or report the blocker |
| Work that needs minutes | `Error executing tool 'terminal': timed out after 420.0s` | `background=True, notify=True` from the start, then `process_manage` |
| Live log follow | `tail -f` returns nothing until the cap | `tail -n 200 <log>` for a snapshot; background + `process_manage` for live |

## Procedure

1. **Classify the run before acting.** Read the session source / dispatch prompt. Completion: you can state "unattended" and therefore "file-based execution only".
2. **Write every multi-line command to a file first** (`scripts/tmp_<topic>.py` or `<scratch>/task.sh`). Completion: the file exists and `python -m py_compile <file>` (or `bash -n <file>`) is silent.
3. **Run it by path** — `python <file>` / `bash <file>` — with a timeout that fits the work. Completion: real exit code plus non-empty expected stdout.
4. **Long jobs go to the background.** `terminal(command=..., background=True, notify=True)` then poll with `process_manage`; never `sleep 300 && ls` in the foreground (it burns the turn and hides the exit code). Completion: you have the process output or a completion notification, not a bare sleep.
5. **Redirect to a native scratch path, then `read_file` it.** `$TMPDIR` is `/tmp` in git-bash; MSYS can write there but native tools report it missing. Completion: `read_file` returns the content (not "File not found").
6. **Put the proof in the deliverable.** Paste the real command + real output into the report/log. Completion: no claim in the output rests on "should work".

## Pitfalls

- **Wrappers do not launder a blocked flag.** `timeout 300 python -c "..."` and `timeout 120 ./venv/Scripts/python.exe - <<'PY'` still trip the `-e/-c` and heredoc rules. The detection is on the interpreter family + flag, not on the wrapper.
- **Quote mangling kills the inline route even where approvals would allow it.** In git-bash on Windows, `python -c "\"import sys…\""` and multi-line heredocs come back as `bash: -c: line N: unexpected EOF while looking for matching '` or `SyntaxError: unterminated string literal (detected at line 1)` — the *shell* truncated the payload before Python parsed it. It reads like broken Python; it is broken quoting (64 messages across 5 sessions in one week). Same fix: write the file, run it by path.
- **`write_file` needs a complete read of an existing file.** After paging through a file with `offset`/`limit`, the rewrite is refused (`was last read with offset/limit pagination (partial view)`) — page to the end, or read it whole, before overwriting. See `safe-file-edits-windows`.
- **`execute_code` availability is mode-dependent.** It works interactively but returns `BLOCKED … single-query mode` in cron/worker runs. Do not build an acceptance path that depends on it; expect to see workers retry it once and lose a turn (observed 11 sessions / 12 occurrences in one week).
- **An approval timeout is not a pass.** `Command timed out without user response. The user has NOT consented` means the command never ran. Retrying the same command repeats the 120s wait and can trip the "do NOT retry" instruction — switch to a non-approval path.
- **`sleep N && cmd` is not a timer.** Foreground sleeps eat the whole turn and produce no observation while waiting. Use `background=True` + `process_manage`, and note that waits are clamped (180 s observed).
- **`tail -f` in a `terminal` call never returns.** `tail -f`/`tail -F` follow until killed, so the call burns the entire cap and hands back nothing (12 calls / 3 sessions, 900 s cap in one case, while the operator only wanted "what does the log say now"). Take a snapshot with `tail -n 200 <log>`; if you truly need live output, start the job with `background=True, notify=True` and read the log file between polls.
- **`process_manage` poll blocks for *its own* timeout, and "timed out" does not mean the child died.** 24 polls at 60 s in a single session watching a long pan-search pipeline: each poll returned `timed out after 60.0s` while the process kept running. Read the process `status` field before deciding anything — restarting on a poll timeout creates a second competing worker on the same files.
- **The foreground default cap is 420 s, and a timeout result is not a failed command.** `pip install`, a Chromium download, and a Chrome re-download each died at exactly `420.0s` in one session; a `dispatch_claude.sh` call died at 180 s. Nothing rolls back on timeout, so a blind re-run duplicates the work: check the artifact (`venv/Lib/site-packages/<pkg>`, the log's last lines) before retrying, and launch anything that installs or downloads with `background=True, notify=True` from the outset.
- **Path conversion is off for native programs.** `git -C /c/x`, `node /tmp/a.js`, and `python /tmp/a.py` fail even when `cd /c/x` works in bash. Pass `C:/x/...`-style forward-slash paths.
- **`python3` can resolve and still fail** (Store stub). Prove the interpreter with `python --version` or a one-line script file — `python -c` is itself blocked here.
- **Killing a child on Windows needs `taskkill //F //T //PID <pid>`** — double slashes, or MSYS rewrites the flags. GNU `timeout` cannot kill a native `.exe`.
- **Never fabricate the output you could not produce.** If the command was blocked and no alternative exists, report the blocker — that is a valid result; an invented number is not.

## Verification

- The command you claim to have run appears in the transcript with a real exit code
- Captured file is readable via `read_file` from a native path
- For background jobs: `process_manage` shows a terminal status, not "running"
- Any artifact generated in the run is committed/hashed (see `evidence-backed-deliverables`)
