---
name: hermes-script-library-safety
description: "Enforce WSL script safety with guard.py and readonly mounts."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [script-safety, wsl, guard, readonly-mount, deploy, python]
    related_skills: [cross-platform-text-processing, debug-wsl-windows-network, manage-python-venv-wsl]
---

# Hermes Script Library Safety

Enforce the Hermes script safety model: WSL-only development, readonly Windows mounts (`/mnt/c`, `/mnt/d`), runtime guard (`tools/guard.py`), utility modules (`fs.py`, `proc.py`, `jsonio.py`), staged execution with dry-run default, and controlled deployment via `deploy_to_prod.sh` with temporary remount.

## When to Use

- Creating new automation scripts in `~/.hermes/python/scripts/`
- Auditing existing scripts for safety compliance
- Setting up the script library structure for the first time
- Debugging script execution failures (guard violations)
- Deploying mature scripts to Windows production path

## Prerequisites

- WSL2 (Ubuntu 24.04) with systemd enabled
- `/etc/wsl.conf` configured with readonly automount
- Python 3.10+ with venv at `~/.hermes/python/.venv/`
- `~/.hermes/python/` directory structure exists

## How to Run

```bash
# 1. Verify safety infrastructure
ls -la /home/user01/.hermes/python/tools/guard.py
ls -la /home/user01/.hermes/python/tools/fs.py
grep "ro,noatime" /etc/wsl.conf

# 2. Create new script (follows template)
cat > /home/user01/.hermes/python/scripts/my_script.py << 'EOF'
import tools.guard  # MUST BE FIRST IMPORT
# ... script body with --dry-run default, --apply to execute
EOF

# 3. Test in WSL (dry-run default)
cd /home/user01/.hermes/python && python scripts/my_script.py

# 4. Deploy to Windows (when mature)
./deploy_to_prod.sh my_script.py
```

## Quick Reference

| Task | Command |
|------|---------|
| Check guard.py | `ls -la ~/.hermes/python/tools/guard.py` |
| Verify readonly mounts | `mount | grep -E "/mnt/c|/mnt/d" | grep ro` |
| Run script (dry-run) | `cd ~/.hermes/python && python scripts/x.py` |
| Run script (apply) | `cd ~/.hermes/python && python scripts/x.py --apply` |
| Deploy to Windows | `~/.hermes/python/deploy_to_prod.sh script.py` |

## Procedure

### 1. Configure WSL Readonly Mounts (one-time)
```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[automount]
options = "ro,noatime,uid=1000,gid=1000,umask=022"
EOF
wsl --shutdown  # Run from Windows PowerShell
```
**Completion criterion:** `mount | grep /mnt/c` shows `ro,noatime`.

### 2. Create Guard Module (`tools/guard.py`)
```python
# ~/.hermes/python/tools/guard.py
import os, sys, pathlib
def _check():
    # 1. Must be in WSL
    if "microsoft" not in open("/proc/version").read().lower():
        sys.exit("Not running in WSL2")
    # 2. CWD must be under ~/.hermes/python
    cwd = pathlib.Path.cwd().resolve()
    allowed = pathlib.Path("~/.hermes/python").expanduser().resolve()
    if not cwd.is_relative_to(allowed):
        sys.exit(f"CWD {cwd} not under {allowed}")
    # 3. /mnt/c and /mnt/d must be readonly
    for mnt in ["/mnt/c", "/mnt/d"]:
        if os.path.exists(mnt):
            with open("/proc/mounts") as f:
                for line in f:
                    if line.startswith(mnt + " ") and "rw," in line:
                        sys.exit(f"{mnt} mounted RW (should be RO)")
_check()
```
**Completion criterion:** Importing `tools.guard` in a script exits with clear error if any check fails.

### 3. Create Utility Modules
```bash
# fs.py - cross-platform path helpers
# proc.py - subprocess wrapper with timeout, JSON output
# jsonio.py - stdout=JSON, stderr=logs standard
```
**Completion criterion:** All three modules import without error.

### 4. Script Template (every script must follow)
```python
#!/usr/bin/env python3
import tools.guard  # FIRST LINE - enforces safety
import argparse, json, sys
from tools import fs, proc, jsonio

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually execute (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only (default)")
    parser.add_argument("--stage", choices=["scan", "plan", "backup", "execute", "verify"])
    parser.add_argument("--checkpoint", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    # Default to dry-run
    if not args.apply:
        args.dry_run = True

    # ... script logic ...
    # On changes: backup first, then execute
    # Output: stdout = JSON result, stderr = human logs
    jsonio.emit({"status": "ok", "dry_run": args.dry_run, "changed": []})

if __name__ == "__main__":
    main()
```
**Completion criterion:** Script runs with `--dry-run` by default, requires `--apply` for mutations.

### 5. Create Deploy Script (`deploy_to_prod.sh`)
```bash
#!/usr/bin/env bash
# ~/.hermes/python/deploy_to_prod.sh
set -euo pipefail
SCRIPT=$1
DEST="/mnt/d/Ai/python/$(basename $SCRIPT)"
# Temporarily remount RW
sudo mount -o remount,rw /mnt/d
cp "$SCRIPT" "$DEST"
sudo mount -o remount,ro /mnt/d
echo "Deployed to $DEST (readonly restored)"
```
**Completion criterion:** Script copies to Windows path, restores readonly mount, logs deployment.

## Pitfalls

- **Guard import order**: Must be **first import** in every script, before stdlib.
- **Mount remount requires sudo**: Deploy script needs passwordless sudo for `mount` (configure `/etc/sudoers.d/wsl-remount`).
- **Windows path differences**: Use `tools.fs.to_win()` / `to_wsl()` for path conversion.
- **Venv activation**: Scripts run with `~/.hermes/python/.venv/bin/python` explicitly.
- **Cron/background scripts**: Must activate venv in shebang or wrapper.

## Verification

```bash
# 1. Guard blocks non-WSL
# (Run script from Windows PowerShell -> should fail)

# 2. Guard blocks wrong CWD
cd /tmp && python ~/.hermes/python/scripts/disk_audit.py 2>&1 | grep "CWD"

# 3. Guard blocks RW mount
# (Temporarily remount RW, run script -> should fail)

# 4. Script defaults to dry-run
python ~/.hermes/python/scripts/disk_audit.py 2>&1 | grep "dry_run.*true"

# 5. Deploy restores readonly
./deploy_to_prod.sh disk_audit.py && mount | grep /mnt/d | grep ro
```

---

*Skill distilled from sessions 20260908_042140_65b6a3aa, 20260908_045154_388088 (3+ occurrences: guard.py design, readonly mount enforcement, deploy_to_prod.sh, utility modules). Pattern threshold >=3 met.*