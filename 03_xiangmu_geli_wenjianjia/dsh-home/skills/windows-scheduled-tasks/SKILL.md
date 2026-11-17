---
name: windows-scheduled-tasks
description: Replace systemd timers with Windows Task Scheduler jobs.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [windows, task-scheduler, schtasks, powershell, scheduling, systemd-replacement]
    related_skills: [hermes-systemd-timers-setup, watchdog-cron-patterns, migrate-hermes-wsl-to-windows, uumit-market-autobid-deployment]
---

# Windows Scheduled Tasks

Register, verify, and remove recurring jobs with Windows Task Scheduler — the native equivalent of a WSL2 `systemd --user` timer. Covers `schtasks` vs PowerShell `Register-ScheduledTask`, the mandatory administrator elevation, and the ASCII-only `.bat` wrapper rule.

## When to Use

- Replacing `~/.config/systemd/user/*.timer` with a Windows equivalent
- A `.bat`/`.ps1` registration "ran" but the task is missing from `schtasks /query`
- Registration fails with `HRESULT 0x80070005` / "拒绝访问" (Access denied)
- Daily or at-startup jobs that must run in the interactive user session
- **Don't use for:** Linux systemd timers (`hermes-systemd-timers-setup`), Hermes' own scheduler (`hermes cron`), or in-session one-offs.

## Prerequisites

- Windows host with `schtasks` on PATH (verify: `terminal(command='cmd.exe /c "schtasks /?"')`).
- **Administrator elevation** — both `schtasks /create` and `Register-ScheduledTask` need it.
- One ASCII-only wrapper `.bat` per task that sets env and calls the real work.

## How to Run

```bash
# Simplest: create a daily task (run from an elevated shell)
cmd.exe /c "schtasks /create /tn \"XianyuPipeline\" /tr \"D:\\proj\\run_daily.bat\" /sc daily /st 02:30 /f"

# Verify
cmd.exe /c "schtasks /query /tn \"XianyuPipeline\" /fo list /v"
```

## Quick Reference

| Goal | Command |
|---|---|
| Create (daily) | `schtasks /create /tn <N> /tr "<abs .bat>" /sc daily /st 02:30 /f` |
| Create (at startup) | `schtasks /create /tn <N> /tr "<abs .bat>" /sc onstart /f` |
| Create (every N min) | `schtasks /create /tn <N> /tr "<abs .bat>" /sc minute /mo 15 /f` |
| Query one | `schtasks /query /tn <N> /fo list /v` |
| Run now | `schtasks /run /tn <N>` |
| Delete | `schtasks /delete /tn <N> /f` |
| Rich settings / logon type | PowerShell `New-ScheduledTaskAction` + `New-ScheduledTaskTrigger` + `Register-ScheduledTask -Force` |

## Procedure

1. **Write an ASCII-only wrapper `.bat`.** Set `PROJECT_DIR`, `PYTHON`, `LOG_DIR`; `cd /d "%PROJECT_DIR%"`; log start/end with the exit code; prepend `%PROJECT_DIR%\venv\Scripts;%PATH%` if child processes must resolve CLIs. *Done when `cmd.exe /c "<wrapper>" <task>` exits 0 and appends a log line.*
2. **Register the task.** Use `schtasks /create …` for simple schedules, or PowerShell `Register-ScheduledTask -Force` when you need `-RunLevel Highest`, interactive logon type, or battery/network settings. *Done when the command returns without error — confirm with step 4, not by exit code alone.*
3. **Elevate if denied.** On `Access denied` / `0x80070005`, do **not** retry the same command. Ship a self-elevating `register_tasks_admin.bat` (re-launches itself via `Start-Process -Verb RunAs`) for the user to double-click, or run from an already-elevated shell. *Done when the elevated run registers the task.*
4. **Verify registration.** `schtasks /query /tn <N> /fo list /v` (or PowerShell `Get-ScheduledTask`) shows the task with State `Ready`. *Done when every expected task name is listed.*
5. **Smoke-run.** `schtasks /run /tn <N>` then check the wrapper's log. *Done when the log shows a fresh run with exit code 0.*

## Pitfalls

- **Registration needs admin.** Un-elevated `Register-ScheduledTask` returns `HRESULT 0x80070005` / 拒绝访问; `schtasks /create` returns "拒绝访问". Elevate; don't loop on the same non-elevated call.
- **`.bat` comments must be ASCII.** cmd.exe parses `.bat` in the OEM codepage (GBK on zh-CN). UTF-8 Chinese `REM` lines produce `'tive' 不是内部或外部命令` and abort the script mid-way. Keep all `REM` text ASCII.
- **Invoke `.bat` through cmd.** `terminal(command='cmd.exe /c "D:\\path\\run.bat"')` — calling the `.bat` from git-bash directly can mis-resolve it.
- **Absent task ≠ crash.** `schtasks /query /tn X` prints "系统找不到指定的文件" (ERROR: The system cannot find the file specified) when the task does not exist — that means "not registered".
- **PATH for MCP/CLI children.** Windows tasks start with a minimal PATH; prepend the venv Scripts dir inside the wrapper so spawned MCP servers can resolve their executables.
- **Silent failures.** A task that exits non-zero is invisible unless the wrapper logs. Always log start/end + exit code.
- **Hermes jobs vs Task Scheduler.** Hermes' built-in `hermes cron` already has its own scheduler; use Task Scheduler for non-Hermes pipelines or `no_agent` script jobs.

## Verification

1. `schtasks /query /tn "<NAME>" /fo list /v` lists each task with State `Ready`.
2. Direct wrapper run exits 0 and writes a log line.
3. PowerShell `Get-ScheduledTask` shows the same task names.
4. `schtasks /run /tn "<NAME>"` produces a fresh log entry.

---

*Distilled from the 2026-10-14 WSL2→Windows migration (schtasks/PowerShell registration attempts, admin-elevation denials, GBK `.bat` breakage, missing-task verification).*
