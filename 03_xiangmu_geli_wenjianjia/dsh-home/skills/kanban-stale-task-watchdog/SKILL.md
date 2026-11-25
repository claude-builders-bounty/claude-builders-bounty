---
name: kanban-stale-task-watchdog
description: Reclaim stuck kanban running tasks via SQLite when worker process is gone.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [kanban, watchdog, stale-task, reclamation, sqlite, cron]
    related_skills: [hermes-wf-kanban-orchestration, watchdog-cron-patterns, unattended-agent-execution, feishu-im-alert]
---

# Kanban Stale Task Watchdog

Cron job pattern that detects `running` kanban cards whose worker process has died (no PID, no recent log output), reclaims them via direct SQLite update, and re-dispatches with review findings attached.

## When to Use

- Kanban board has cards stuck in `running` for >15 minutes with no worker logs
- Cron sentinel logs show `tick rc=0` but `ready` cards never get dispatched (slots occupied by zombies)
- Need automated, no-human-intervention recovery for unattended kanban workers

**Don't use for:** Cards that are legitimately slow (NVIDIA upstream can take 5+ minutes per request) — verify via upstream request logs first.

## Prerequisites

- Access to kanban SQLite DB: `D:/Ai/Agent/hermes/kanban/boards/<board>/kanban.db`
- Worker log directory: `logs/workers/<task_id>.out` (mtime is the only reliable liveness signal)
- `hermes` CLI in PATH for `reclaim` command (preferred over raw SQL)

## Quick Reference

```bash
# Detect stale running tasks (mtime > 15 min, or no log file)
python stale_watchdog.py --board xianyu --stale-seconds 900

# Reclaim single task via CLI (writes task_events)
hermes kanban --board xianyu reclaim t_abc123 --reason "巡检自愈：worker 日志超 15 分钟无输出"

# Reclaim via direct SQLite (when CLI unavailable)
sqlite3 kanban.db "UPDATE tasks SET status='ready' WHERE id='t_abc123' AND status='running';"
sqlite3 kanban.db "INSERT INTO task_events(task_id,kind,created_at,detail) VALUES('t_abc123','reclaimed',strftime('%s','now'),'worker log mtime > 900s');"

# Verify reclamation
hermes kanban --board xianyu show t_abc123 --json
```

## Procedure

### 1. Identify Stale Running Tasks

```python
import sqlite3, os, time

DB = r"D:/Ai/Agent/hermes/kanban/boards/xianyu/kanban.db"
LOG_DIR = r"D:/Ai/Agent/hermes/scripts/hermes-wf-xianyu/logs/workers"
STALE_SECONDS = 900  # 15 minutes

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
running = con.execute("SELECT id, worker_pid, started_at FROM tasks WHERE status='running'").fetchall()

now = time.time()
stale = []
for row in running:
    tid = row["id"]
    log_path = os.path.join(LOG_DIR, f"{tid}.out")
    
    # No log file = dispatch failed residue
    if not os.path.exists(log_path):
        stale.append((tid, "no log file"))
        continue
    
    # Log mtime > STALE_SECONDS = worker dead
    mtime = os.path.getmtime(log_path)
    if now - mtime > STALE_SECONDS:
        stale.append((tid, f"log mtime {now - mtime:.0f}s ago"))

print(f"Stale tasks: {stale}")
```

**Completion criterion:** List of `(task_id, reason)` pairs where each task is verifiably dead (no process, no recent log output).

### 2. Reclaim via CLI (Preferred)

```bash
for tid in t_abc123 t_def456; do
  hermes kanban --board xianyu reclaim "$tid" --reason "巡检自愈：worker 日志超 15 分钟无输出"
done
```

**Completion criterion:** `hermes kanban show <tid> --json` returns `"status": "ready"` for each reclaimed task.

### 3. Reclaim via Direct SQLite (Fallback)

```python
for tid, reason in stale:
    con.execute("UPDATE tasks SET status='ready' WHERE id=? AND status='running'", (tid,))
    con.execute(
        "INSERT INTO task_events(task_id,kind,created_at,detail) VALUES(?,?,?,?)",
        (tid, "reclaimed", int(time.time()), reason)
    )
con.commit()
```

**Completion criterion:** Same as step 2, plus `task_events` row exists with `kind='reclaimed'`.

### 4. Attach Review Findings Before Re-dispatch

```python
# Read review document if exists
review_path = f"D:/Ai/Agent/hermes/scripts/hermes-wf-xianyu/docs/REVIEW_{tid}.md"
if os.path.exists(review_path):
    with open(review_path, encoding="utf-8") as f:
        review = f.read()
    
    # Append to card body via SQLite (kanban edit --body truncates multi-line)
    con.execute("UPDATE tasks SET body = body || '\n\n## Review Findings (Auto-Attached)\n' || ? WHERE id=?", (review, tid))
    con.commit()
```

**Completion criterion:** Card body contains the review findings; next sentinel tick auto-dispatches the task.

### 5. Verify Re-dispatch

```bash
# Wait one sentinel tick (2 min on this machine), then verify
sleep 120
hermes kanban --board xianyu list --status running
# Should show the reclaimed task now with a worker_pid
```

**Completion criterion:** Task moves from `ready` → `running` with a valid `worker_pid` within one sentinel interval.

## Pitfalls

- **Never use `started_at` or `claim_expires` for staleness.** `started_at` does NOT refresh on re-claim; a 10-minute-old task can show 11 hours. `claim_expires` is unreliable when dispatcher writes DB directly without CLI lease renewal.
- **Only trust `logs/workers/<tid>.out` mtime.** This is the only signal that changes while the worker is actually producing output.
- **Don't reclaim tasks with active upstream requests.** Check `cc-switch` proxy logs: if `proxy_request_logs` has new rows for the task's session in the last 5 minutes, the worker is alive but slow (NVIDIA upstream). Wait longer.
- **`hermes kanban reclaim` is the correct CLI** — it writes `task_events` automatically. Raw `UPDATE tasks` breaks the audit trail unless you also insert a `reclaimed` event row in the same transaction.
- **Card body updates must go through SQLite**, not `kanban edit --body`. The CLI truncates multi-line bodies to the last line (or fails with `rc=2` if body starts with `---`).

## Verification

```bash
# 1. Run detection — should find zero stale tasks after watchdog runs
python stale_watchdog.py --board xianyu --stale-seconds 900
# Expected: "Stale tasks: []"

# 2. Verify no running tasks without worker_pid
sqlite3 kanban.db "SELECT id, worker_pid FROM tasks WHERE status='running' AND (worker_pid IS NULL OR worker_pid=0);"
# Expected: empty result

# 3. Verify audit trail
sqlite3 kanban.db "SELECT task_id, kind, detail FROM task_events WHERE kind='reclaimed' ORDER BY created_at DESC LIMIT 5;"
# Expected: recent reclaimed entries with reasons

# 4. Verify re-dispatched tasks have commits
# (run after one sentinel cycle)
git -C <repo> log --since="10 minutes ago" --oneline --grep="t_" | head -5
# Expected: commits with task IDs
```

## Reference Implementation

See `scripts/kanban_stale_watchdog.py` in this skill's directory for the complete watchdog script used in production (job_id: `558ac3922cdf`, runs every ~7 minutes via Windows Task Scheduler).

---

*Distilled from 2026-10-27 cron runs (job `558ac3922cdf`): 10+ executions in one day, each detecting and reclaiming 1-2 stuck `running` tasks on `window_tool` and `xianyu` boards. The `reclaim` CLI + review-findings attachment pattern prevented 22+ hours of stalled pipeline time.*