---
name: clean-windows-c-drive
description: "Free space on Windows C: drive via safe cleanup."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [disk-cleanup, windows, c-drive, maintenance, monitoring]
    related_skills: [proactive-health-patrol, diagnose-ollama-wsl-connectivity, wsl-readonly-mount-enforcement]
---

# Clean Windows C: Drive

Automated and manual procedures to reclaim space on the Windows C: drive when usage exceeds thresholds (default 85%). Designed for WSL2 environments where C: is mounted at `/mnt/c` with readonly enforcement.

## When to Use

- Health patrol reports `Disk /mnt/c` at or above 85% usage
- Windows updates fail due to insufficient space
- Application installs fail with disk full errors
- Proactive maintenance before threshold breach

## Prerequisites

- WSL2 with `/mnt/c` mounted (readonly or read-write via `deploy_to_prod.sh`)
- `hermes-agent` config with `disk.mnt_c_threshold: 85` (default)
- Administrator PowerShell for some cleanup operations
- `cleanmgr` (Disk Cleanup) available on Windows

## How to Run

```bash
# Quick check from WSL
df -h /mnt/c

# Full cleanup workflow (run from WSL)
hermes chat -q "Run C: drive cleanup: check usage, clean temp, logs, downloads, report remaining"

# Or manual PowerShell (Admin)
# See Quick Reference for commands
```

## Quick Reference

| Task | Command | Context |
|------|---------|---------|
| Check C: usage | `df -h /mnt/c` | WSL |
| Check C: usage | `Get-CimInstance Win32_LogicalDisk | Where-Object {$_.DeviceID -eq 'C:'} | Select-Object @{Name='Free(GB)';Expression={"{0:N2}" -f ($_.FreeSpace/1GB)}}, @{Name='Size(GB)';Expression={"{0:N2}" -f ($_.Size/1GB)}}, @{Name='Used%';Expression={"{0:P0}" -f (1-$_.FreeSpace/$_.Size)}}` | PowerShell |
| Clean user temp | `Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell |
| Clean system temp | `Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell (Admin) |
| Clean Windows Update cache | `Remove-Item -Path "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell (Admin) |
| Clean Delivery Optimization | `Remove-Item -Path "C:\Windows\DeliveryOptimization\Download\*" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell (Admin) |
| Run Disk Cleanup (interactive) | `cleanmgr /sagerun:1` | PowerShell |
| Find large folders | `Get-ChildItem C:\ -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.Length -gt 1GB} | Sort-Object Length -Descending | Select-Object FullName, @{Name='Size(GB)';Expression={"{0:N2}" -f ($_.Length/1GB)}} | Format-Table -AutoSize` | PowerShell (Admin) |
| Scan AppData\Local | `Get-ChildItem "$env:LOCALAPPDATA" -Directory | ForEach-Object { $s=(Get-ChildItem $_.FullName -Recurse -EA 0 | Measure-Object Length -Sum).Sum/1MB; [PSCustomObject]@{Name=$_.Name; SizeMB=[math]::Round($s,2)} } | Sort SizeMB -Desc | Select -First 20` | PowerShell |
| Scan AppData\Roaming | `Get-ChildItem "$env:APPDATA" -Directory | ForEach-Object { $s=(Get-ChildItem $_.FullName -Recurse -EA 0 | Measure-Object Length -Sum).Sum/1MB; [PSCustomObject]@{Name=$_.Name; SizeMB=[math]::Round($s,2)} } | Sort SizeMB -Desc | Select -First 20` | PowerShell |
| Clean Doubao cache | `Remove-Item -Path "$env:LOCALAPPDATA\Doubao" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell |
| Clean LarkShell cache | `Remove-Item -Path "$env:APPDATA\LarkShell" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell |
| Clean duowan cache | `Remove-Item -Path "$env:APPDATA\duowan" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell |
| Clean Thunder Network cache | `Remove-Item -Path "$env:LOCALAPPDATA\Thunder Network" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell |
| Clean Kingsoft/WPS cache | `Remove-Item -Path "$env:APPDATA\Kingsoft" -Recurse -Force -ErrorAction SilentlyContinue` | PowerShell |

## Procedure

### 1. Assess Current Usage

```bash
# From WSL (readonly-safe)
df -h /mnt/c
# Output: Filesystem      Size  Used Avail Use% Mounted on
#         /dev/sdX        81G   68G   13G  85% /mnt/c
```

**Completion criterion**: Usage percentage confirmed; if ≥85%, proceed.

### 2. Identify Top Space Consumers

```bash
# From WSL (readonly-safe, limited to accessible paths)
sudo du -h /mnt/c/Users --max-depth=2 2>/dev/null | sort -hr | head -20
sudo du -h /mnt/c/Windows --max-depth=2 2>/dev/null | sort -hr | head -20
sudo du -h /mnt/c/ProgramData --max-depth=2 2>/dev/null | sort -hr | head-10
```

**Completion criterion**: Top 5 directories by size identified.

### 3. Safe Cleanup Targets (Priority Order)

| Priority | Target | Risk | Command |
|----------|--------|------|---------|
| 1 | User `%TEMP%` | None | `Remove-Item "$env:TEMP\*" -Recurse -Force` |
| 2 | System `C:\Windows\Temp` | Low | `Remove-Item "C:\Windows\Temp\*" -Recurse -Force` |
| 3 | Windows Update download cache | None (re-downloads) | `Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force` |
| 4 | Delivery Optimization cache | Low (re-downloads) | `Remove-Item "C:\Windows\DeliveryOptimization\Download\*" -Recurse -Force` |
| 5 | Browser caches (Chrome/Edge/Firefox) | Low (rebuilds) | Per-browser clear cache |
| 6 | AppData\Local\Doubao (豆包) | None | `Remove-Item "$env:LOCALAPPDATA\Doubao" -Recurse -Force` |
| 6 | AppData\Roaming\LarkShell (飞书) | None | `Remove-Item "$env:APPDATA\LarkShell" -Recurse -Force` |
| 6 | AppData\Roaming\duowan (多玩/YY) | None | `Remove-Item "$env:APPDATA\duowan" -Recurse -Force` |
| 6 | AppData\Local\Thunder Network (迅雷) | Low | `Remove-Item "$env:LOCALAPPDATA\Thunder Network" -Recurse -Force` |
| 6 | AppData\Roaming\Kingsoft (WPS) | Low | `Remove-Item "$env:APPDATA\Kingsoft" -Recurse -Force` |
| 7 | Downloads folder (user review) | **Manual** | Review `C:\Users\<user>\Downloads` |
| 8 | Recycle Bin | None | `Clear-RecycleBin -Force` |
| 9 | Windows.old (post-upgrade) | **Manual** | `cleanmgr` → "Previous Windows installations" |

**Completion criterion**: Each target cleaned; space reclaimed logged.

### 4. Advanced Cleanup (If Still ≥85%)

```powershell
# Find files >1GB (run as Admin)
Get-ChildItem C:\ -Recurse -ErrorAction SilentlyContinue `
  | Where-Object {$_.Length -gt 1GB} `
  | Sort-Object Length -Descending `
  | Select-Object FullName, @{Name='Size(GB)';Expression={"{0:N2}" -f ($_.Length/1GB)}} `
  | Format-Table -AutoSize

# Check for large logs
Get-ChildItem "C:\Windows\Logs" -Recurse -ErrorAction SilentlyContinue `
  | Where-Object {$_.Length -gt 100MB} `
  | Sort-Object Length -Descending
```

**Completion criterion**: Large files identified; decision made (delete/move/archive).

### 5. Verify & Report

```bash
# Post-cleanup check
df -h /mnt/c
# Report: "C: drive usage: 85% → 72% (reclaimed 13GB)"
```

**Completion criterion**: Usage below threshold (default <80%), JSON report generated.

## Pitfalls

| Issue | Solution |
|-------|----------|
| `/mnt/c` readonly in WSL | Run cleanup commands in **PowerShell (Admin)** on Windows, not WSL |
| Permission denied on system folders | Requires Administrator PowerShell; some files locked by system — skip those |
| `cleanmgr` requires interactive session | Use `/sagerun:N` with pre-configured profiles, or run manually |
| Space rebounds quickly | Check for runaway logs (Docker, application), move data to D:, expand C: |
| WSL `du` slow on /mnt/c | Use PowerShell `Get-ChildItem` for targeted searches instead |
| PowerShell foreach syntax in Chinese locale | Use `foreach ($f in $folders)` not `foreach ( in )` — latter throws `MissingVariableNameAfterForeach` |

## Verification

```bash
# 1. Usage below threshold
df -h /mnt/c | awk 'NR==2 {print $5}' | sed 's/%//' | xargs -I{} test {} -lt 80 && echo "PASS: <80%"

# 2. Structured report exists
test -f /home/user01/.hermes/logs/c_drive_cleanup_$(date +%Y%m%d).json && echo "Report saved"

# 3. No critical errors in cleanup
grep -c "FAIL" /home/user01/.hermes/logs/c_drive_cleanup_$(date +%Y%m%d).json
# Should be 0 or only expected "file in use" skips
```

---

*Distilled from 5+ health patrol cron runs (Sep 25-Oct 2, 2026) where C: drive consistently reported 85% usage. Pattern: Windows temp, update cache, and Delivery Optimization caches are primary reclaimable targets. Root cause: no automated cleanup schedule on Windows host.*