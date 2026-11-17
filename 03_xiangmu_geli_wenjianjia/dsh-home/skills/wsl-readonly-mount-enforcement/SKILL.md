---
name: wsl-readonly-mount-enforcement
description: Enforce readonly mounts for /mnt/c and /mnt/d via wsl.conf.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [wsl, readonly-mount, security, isolation, wsl-conf]
    related_skills: [debug-wsl-windows-network, cross-platform-text-processing, hermes-script-library-safety]
---

# WSL Readonly Mount Enforcement

Enforce kernel-level readonly mounts for Windows drives (`/mnt/c`, `/mnt/d`) via `/etc/wsl.conf` to prevent any script or process from modifying the Windows host filesystem. Complements `tools/guard.py` runtime checks.

## When to Use

- Initial WSL2 setup for Hermes
- After `hermes-full-health-check` reports RW mounts
- When security audit requires host isolation
- Before deploying scripts that assume readonly mounts
- After WSL updates that may reset mount options

## Prerequisites

- WSL2 (Ubuntu 24.04) with systemd enabled
- sudo access to edit `/etc/wsl.conf`
- Ability to run `wsl --shutdown` from Windows

## How to Run

```bash
# Apply readonly mounts
hermes skill run wsl-readonly-mount-enforcement --apply

# Verify current mount state
hermes skill run wsl-readonly-mount-enforcement --verify

# Revert to RW (if needed)
hermes skill run wsl-readonly-mount-enforcement --revert
```

## Quick Reference

| Task | Command |
|------|---------|
| Apply readonly | `hermes skill run wsl-readonly-mount-enforcement --apply` |
| Verify mounts | `hermes skill run wsl-readonly-mount-enforcement --verify` |
| Revert to RW | `hermes skill run wsl-readonly-mount-enforcement --revert` |
| Manual check | `mount | grep -E "/mnt/c|/mnt/d"` |

## Procedure

### 1. Check Current Mount State
```bash
mount | grep -E "/mnt/c|/mnt/d"
# RW: shows "rw,noatime" or "rw,relatime"
# RO: shows "ro,noatime"
```
**Completion criterion:** Identify current state before change.

### 2. Configure /etc/wsl.conf for Readonly
```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[automount]
options = "ro,noatime,uid=1000,gid=1000,umask=022"
enabled = true
root = /mnt
EOF
```
**Completion criterion:** File written with `ro,noatime` options.

### 3. Restart WSL to Apply
```bash
# From Windows PowerShell / CMD:
wsl --shutdown
# Then reopen WSL terminal
```
**Completion criterion:** New WSL session shows readonly mounts.

### 4. Verify Readonly Enforcement
```bash
mount | grep -E "/mnt/c|/mnt/d" | grep "ro,noatime"
# Should show both mounts with ro,noatime

# Test write fails
touch /mnt/c/test_write 2>&1 | grep "Read-only"
touch /mnt/d/test_write 2>&1 | grep "Read-only"
```
**Completion criterion:** Mounts show `ro,noatime`, write attempts fail with "Read-only file system".

### 5. Verify Guard.py Integration
```bash
# Ensure guard.py checks mount state
grep -A5 "mnt.*rw" /home/user01/.hermes/python/tools/guard.py
# Should have check for RW mounts
```
**Completion criterion:** Guard module validates readonly at runtime.

### 6. (Optional) Revert to RW for Specific Operations
```bash
# Temporary remount for deployment
sudo mount -o remount,rw /mnt/d
# ... perform deployment ...
sudo mount -o remount,ro /mnt/d
```
**Completion criterion:** Mount temporarily RW, then restored to RO.

## Pitfalls

- **wsl --shutdown required**: Changes to `/etc/wsl.conf` only take effect after full WSL shutdown (not just closing terminal).
- **Windows Fast Startup**: May interfere with clean shutdown; disable in Windows Power Options if issues persist.
- **Deploy script needs sudo**: `deploy_to_prod.sh` requires passwordless sudo for `mount -o remount`. Configure `/etc/sudoers.d/wsl-remount`:
  ```
  user01 ALL=(ALL) NOPASSWD: /bin/mount -o remount,rw /mnt/d, /bin/mount -o remount,ro /mnt/d
  ```
- **Some tools expect RW**: Legacy scripts may fail; update them to use deploy flow.
- **Docker/VM mounts**: Separate from automount; unaffected by this setting.

## Verification

```bash
# 1. Mounts show readonly
mount | grep -E "/mnt/c|/mnt/d" | grep -q "ro,noatime" && echo "PASS" || echo "FAIL"

# 2. Write test fails
touch /mnt/c/test 2>&1 | grep -q "Read-only" && echo "PASS" || echo "FAIL"

# 3. Guard.py validates
python3 -c "import tools.guard; print('Guard OK')" 2>&1 | grep -q "Guard OK" && echo "PASS" || echo "FAIL"

# 4. wsl.conf has correct config
grep -A2 "automount" /etc/wsl.conf | grep -q "ro,noatime" && echo "PASS" || echo "FAIL"
```

---

*Skill distilled from sessions 20260908_042140_65b6a3aa, 20260908_045154_388088 (2+ occurrences: health check SEC-003, script safety discussion, guard.py design). Pattern threshold met via recurring security requirement.*