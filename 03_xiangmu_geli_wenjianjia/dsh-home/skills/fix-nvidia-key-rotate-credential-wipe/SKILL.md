---
name: fix-nvidia-key-rotate-credential-wipe
description: "Fix nvidia-key-rotate wiping .env credentials on WSL boot."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [nvidia, key-rotate, credentials, env, systemd, bug-fix]
    related_skills: [fix-feishu-credentials-sync, manage-systemd-services-wsl, configure-feishu-gateway]
---

# Fix NVIDIA Key Rotate Credential Wipe

Resolve the root cause where `nvidia-key-rotate.service` (with `Persistent=true`) overwrites the entire `~/.hermes/.env` file on every WSL boot, deleting Feishu, ModelScope, and other credentials. The fix makes `update_env()` update only the NVIDIA line while preserving all other keys.

## When to Use

- Feishu/ModelScope credentials keep disappearing from `~/.hermes/.env` after WSL restart
- `nvidia-key-rotate.service` runs on boot (Persistent=true + missed schedule)
- Gateway fails with "app_id or app_secret not found" after WSL reboot
- Credentials present in empress profile but missing from default profile

**Don't use for:**
- Initial credential setup (use `configure-feishu-gateway`)
- Non-NVIDIA credential issues

## Prerequisites

- `nvidia-key-rotate.service` installed at `~/.config/systemd/user/`
- `nvidia_key_rotator.py` at `~/.hermes/credentials/nvidia_key_rotator.py`
- WSL2 with systemd enabled
- NVIDIA API key configured

## How to Run

```bash
# Quick fix (one-liner - patches the rotator script)
sed -i '37,57c\    def update_env(self, new_key: str):\n        env_path = Path.home() / ".hermes" / ".env"\n        lines = env_path.read_text().splitlines() if env_path.exists() else []\n        # Update or add NVIDIA_API_KEY line\n        found = False\n        for i, line in enumerate(lines):\n            if line.startswith("NVIDIA_API_KEY="):\n                lines[i] = f"NVIDIA_API_KEY={new_key}"\n                found = True\n                break\n        if not found:\n            lines.append(f"NVIDIA_API_KEY={new_key}")\n        env_path.write_text("\\n".join(lines) + "\\n")\n        # Also update systemd drop-in\n        dropin = Path.home() / ".config" / "systemd" / "user" / "hermes-gateway.service.d" / "nvidia-api.conf"\n        dropin.parent.mkdir(parents=True, exist_ok=True)\n        dropin.write_text(f"[Service]\\nEnvironment=NVIDIA_API_KEY={new_key}\\n")' ~/.hermes/credentials/nvidia_key_rotator.py

# Verify the fix
grep -A 15 "def update_env" ~/.hermes/credentials/nvidia_key_rotator.py

# Test rotation (dry run - doesn't actually rotate)
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/credentials/nvidia_key_rotator.py --dry-run 2>&1 | head -20
```

## Quick Reference

| Task | Command |
|------|---------|
| View rotator script | `cat ~/.hermes/credentials/nvidia_key_rotator.py` |
| Check service status | `systemctl --user status nvidia-key-rotate` |
| Check timer | `systemctl --user list-timers nvidia-key-rotate` |
| Patch rotator (fix) | See How to Run above |
| Verify fix | `grep -A 15 "def update_env" ~/.hermes/credentials/nvidia_key_rotator.py` |
| Manually rotate key | `systemctl --user start nvidia-key-rotate` |
| Check .env after rotation | `grep -E '^(FEISHU|MODELSCOPE|NVIDIA)_' ~/.hermes/.env` |

## Procedure

### 1. Diagnose the Issue

**Completion criterion**: Confirm `nvidia_key_rotator.py` uses full-file overwrite in `update_env()`.

```bash
cat ~/.hermes/credentials/nvidia_key_rotator.py | grep -A 20 "def update_env"
# If it shows: env_path.write_text(f"NVIDIA_API_KEY={key}") — THAT'S THE BUG
```

### 2. Check Service Configuration

**Completion criterion**: Confirm `Persistent=true` on timer (causes boot-time runs).

```bash
systemctl --user cat nvidia-key-rotate.timer | grep -E "Persistent|OnCalendar"
# Expected: OnCalendar=18:43 and Persistent=true
```

### 3. Apply the Fix

**Completion criterion**: `update_env()` now preserves all non-NVIDIA lines.

```bash
# Backup original
cp ~/.hermes/credentials/nvidia_key_rotator.py ~/.hermes/credentials/nvidia_key_rotator.py.bak

# Apply patch (see How to Run for exact sed command)
# The fix:
# - Reads existing .env
# - Updates ONLY the NVIDIA_API_KEY line
# - Preserves all other lines (FEISHU_*, MODELSCOPE_*, etc.)
# - Writes back complete file
# - Also updates systemd drop-in for gateway
```

### 4. Verify the Fix Works

**Completion criterion**: After simulated rotation, all credentials intact.

```bash
# 1. Ensure .env has all credentials before test
grep -E '^(FEISHU|MODELSCOPE|NVIDIA)_' ~/.hermes/.env
# Should show 6+ lines

# 2. Run rotator in test mode (if --dry-run added) or manually call update_env
~/.hermes/hermes-agent/venv/bin/python -c "
import sys
sys.path.insert(0, '/home/user01/.hermes/credentials')
from nvidia_key_rotator import NvidiaKeyRotator
r = NvidiaKeyRotator()
r.update_env('test-key-12345')
print('Updated')
"

# 3. Verify all credentials still present
grep -E '^(FEISHU|MODELSCOPE|NVIDIA)_' ~/.hermes/.env
# Should still show 6+ lines, with NVIDIA_API_KEY=test-key-12345
```

### 5. Restart Gateway to Pick Up Updated Drop-in

**Completion criterion**: Gateway active with all credentials loaded.

```bash
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
sleep 3
systemctl --user status hermes-gateway --no-pager | grep Active
# Expected: active (running)
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **Script at different path** | Check `systemctl --user cat nvidia-key-rotate` for `ExecStart` path |
| **No `--dry-run` flag** | Add it to the script or test with a Python one-liner as shown |
| **Empress profile separate** | Empress uses `~/.hermes/profiles/empress/.env` — fix applies to default profile |
| **Timer still fires on boot** | `Persistent=true` is intentional (catches missed runs); the fix makes it safe |
| **Multiple gateway services** | Ensure only ONE Feishu gateway runs (disable empress if using default) |

## Verification

```bash
# 1. Fix applied to script
grep -A 15 "def update_env" ~/.hermes/credentials/nvidia_key_rotator.py | grep -q "found = False" && echo "✅ Fix applied"

# 2. All credentials preserved after test rotation
~/.hermes/hermes-agent/venv/bin/python -c "
import sys
sys.path.insert(0, '/home/user01/.hermes/credentials')
from nvidia_key_rotator import NvidiaKeyRotator
r = NvidiaKeyRotator()
r.update_env('verify-key')
"
grep -c '^FEISHU_' ~/.hermes/.env | grep -q '^4$' && echo "✅ 4 FEISHU vars preserved"
grep -c '^MODELSCOPE' ~/.hermes/.env | grep -q '^[1-9]' && echo "✅ MODELSCOPE vars preserved"
grep '^NVIDIA_API_KEY=verify-key' ~/.hermes/.env && echo "✅ NVIDIA key updated"

# 3. Gateway healthy
systemctl --user is-active hermes-gateway | grep -q active && echo "✅ Gateway running"

# 4. Feishu WebSocket connected (check logs)
journalctl --user -u hermes-gateway -n 30 --no-pager | grep -q "connected to wss://msg-frontier.feishu.cn" && echo "✅ Feishu connected"
```

---

*Distilled from session 20261001_043926_d1dae82b (Oct 1, 2026) — root cause analysis of recurring Feishu credential loss across 4+ incidents (Sep 24, 25, 26×2, 30). The `nvidia-key-rotate.service` with `Persistent=true` was firing on every WSL boot and its `update_env()` method used `write_text(f"NVIDIA_API_KEY={key}")` which overwrote the entire `.env` file, deleting all other credentials. Fixed by making `update_env()` preserve non-NVIDIA lines.*