---
name: migrate-hermes-wsl-to-windows
description: Migrate Hermes from WSL2 to native Windows.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [migration, wsl2, windows, paths, scheduler, config]
    related_skills: [windows-scheduled-tasks, edit-config-files-wsl, troubleshoot-hermes-config, hermes-full-health-check, wsl2-windows-interop-automation]
---

# Migrate Hermes From WSL2 To Native Windows

Move a Hermes agent — config, memory files, cron schedule, and its companion Python projects — off WSL2 onto native Windows without leaving stale Linux paths behind or running two schedulers at once. Covers the config/memory rewrite, the systemd → Task Scheduler handoff, and porting project code that hardcoded `/home/...` paths.

## When to Use

- User says "you are on Windows now, stop using WSL2" / "适配 Windows，别动 WSL2"
- `config.yaml`, `MEMORY.md`, `SOUL.md`, `USER.md` still reference `~/.hermes` (Linux), `/mnt/d/...`, `http://172.24.160.1:11434`, or `systemctl --user`
- Windows jobs never fire because the work was registered as WSL systemd timers
- A project under a Windows dir still imports `/home/<user>/...`, uses `.venv/bin`, or hardcodes `/mnt/` paths
- **Don't use for:** driving Windows binaries from WSL2 (that is `wsl2-windows-interop-automation`), or a one-off file copy.

## Prerequisites

- Hermes installed natively on Windows; `terminal(command="hermes config --help")` prints `show/edit/get/set/unset/path/env-path/check/migrate`.
- The WSL distro is still installed and readable (`terminal(command="wsl --list --quiet")`) so the Linux source can be read.
- **Both sides stay isolated.** Read the WSL Hermes read-only; never write to it during migration.
- Administrator available for Task Scheduler registration (see `windows-scheduled-tasks`).

## How to Run

Order matters: audit → rewrite Windows config + memory → port projects → replace the scheduler → verify isolation.

```bash
# 1. Audit: what does each side claim?
hermes config show
# read the Windows-side memory/config files with read_file
# 2. Find every WSL leftover in the live tree
search_files(pattern="/home/|/mnt/|172\\.24\\.160\\.1|systemctl --user|~/.hermes", path="<HERMES_HOME>")
```

## Quick Reference

| Concern | Windows-native form |
|---|---|
| Edit Hermes config | `hermes config set <key> <value>` (CLI) — `patch`/`write_file` **refuse** `config.yaml` |
| Ollama endpoint | `http://127.0.0.1:11434` (not the WSL vEthernet IP) |
| ChromaDB persist dir | `<HERMES_HOME>\chroma\` (Windows path, no `/mnt/`) |
| Scheduler | Windows Task Scheduler (`windows-scheduled-tasks`), not `systemctl --user` |
| Read WSL files | `\\wsl.localhost\<DISTRO>\home\<user>\...` via cmd.exe/PowerShell |
| venv layout | `venv\Scripts\python.exe` (not `.venv/bin/python`) |

## Procedure

1. **Audit both sides.** Run `hermes config show`; `read_file` the Windows `config.yaml`, `SOUL.md`, `USER.md`, `MEMORY.md`; check `cron/jobs.json` and `hermes cron list`. *Done when you can list every WSL reference in the Windows config and every job's scheduler.*

2. **Rewrite the Windows Hermes config via the CLI.**
   ```bash
   hermes config set auxiliary.vision.provider ollama
   hermes config set auxiliary.vision.base_url http://127.0.0.1:11434
   hermes config set auxiliary.vision.model qwen2.5-vl:7b
   ```
   Never edit `config.yaml` with `patch`/`write_file`, and never with ad-hoc line-oriented shell edits — the Hermes tools refuse it and line edits corrupt YAML (see Pitfalls). *Done when `hermes config get <key>` returns the Windows value and `config.yaml` still parses.*

3. **Update the memory / identity files.** Fix every path and scheduler reference in `SOUL.md`, `USER.md`, `MEMORY.md`. There are usually **two** copies — `<HERMES_HOME>/MEMORY.md` and `<HERMES_HOME>/memories/MEMORY.md` — update both. *Done when a `search_files` scan for `/mnt/|172\.24\.160\.1|systemctl` finds no live config/memory hits.*

4. **Port companion projects.** For each project moved out of WSL: replace `/home/...`, `/mnt/...`, `.venv/bin` with Windows equivalents; add root auto-detection (`PIPELINE_ROOT = Path(__file__).resolve().parent.parent`); add cross-platform font fallbacks (`C:/Windows/Fonts/msyh.ttc`); prepend `venv\Scripts` to `PATH` where child processes must resolve CLIs. Copy the tree from WSL over a UNC path:
   ```bash
   cmd.exe /c "robocopy \\wsl.localhost\<DISTRO>\home\<user>\<proj> D:\path\to\<proj> /E /I /Y"
   ```
   *Done when a `search_files` scan of the project finds no `/home/|/mnt/|\.venv/bin` and the entry point runs (exit 0).*

5. **Replace the scheduler.** Migrate each WSL `systemd --user` timer/service to a Windows scheduled task using `windows-scheduled-tasks`. *Done when `schtasks /query /tn <NAME>` returns every expected task.*

6. **Verify isolation.** Re-read the WSL side read-only (`wsl -d <DISTRO> -- bash -c "ls -la /home/<user>/.hermes"`); confirm nothing there changed. *Done when the WSL install is unchanged and only the Windows side carries the new configuration.*

## Pitfalls

- **`patch`/`write_file` refuse `config.yaml`.** Error: `Refusing to write to Hermes config file … Agent cannot modify security-sensitive configuration.` Use `hermes config set/get/unset/edit`.
- **Line-oriented shell edits wreck YAML.** Applying a stream editor to `config.yaml` duplicates keys (e.g. three `compression:` blocks) and yields `mapping values are not allowed here`; Hermes then logs `Failed to process config.yaml — falling back to .env / gateway.json values` and silently ignores the file. Always validate after a manual edit.
- **Two memory files.** `<HERMES_HOME>/MEMORY.md` and `<HERMES_HOME>/memories/MEMORY.md` are separate; updating one leaves the stale copy live.
- **The WSL vEthernet IP (`172.24.160.1`) is dead weight on native Windows.** Point Ollama at `127.0.0.1`.
- **`//wsl.localhost/` is not a git-bash path.** Use the UNC form `\\wsl.localhost\<DISTRO>\...` inside `cmd.exe`/PowerShell (`robocopy`, `Copy-Item`); `ls //wsl.localhost/` returns "No such file or directory".
- **Don't touch the WSL Hermes.** The user wants both installs isolated; a migration that mutates the source is a bug.
- **Pin Hermes cron jobs explicitly.** An unpinned cron job is skipped when the global model changes (`drift_skip`, job stuck at `last_status: error`); re-pin with `hermes cron edit <job_id> --provider <p> --model <m>`.
- **Copying `.env` mirrors secrets.** Move credentials by value, never echo them into logs or the skill (zero-plaintext rule).

## Verification

1. `hermes config get <key>` returns Windows values; `python -c "import yaml;yaml.safe_load(open('config.yaml'))"` exits 0 (in cron, write a `.py` and run it instead of `-c`).
2. `search_files(pattern="/mnt/|172\\.24\\.160\\.1|systemctl --user", path="<HERMES_HOME>")` → no hits in live config/memory (historical logs may still match).
3. `schtasks /query /tn "<NAME>"` returns each migrated task.
4. Each ported project's entry point runs with exit 0.
5. `wsl -d <DISTRO> -- bash -c "ls -la /home/<user>/.hermes"` shows the WSL install unchanged.

---

*Distilled from the 2026-10-14 WSL2→Windows native migration session (426 messages, 204 tool calls: config CLI rewrite, dual MEMORY.md sync, robocopy via \\wsl.localhost, project path porting, systemd→schtasks handoff).*
