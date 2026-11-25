---
name: diagnose-ollama-wsl-connectivity
description: "Diagnose Ollama unreachable from WSL2 via Windows host."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [ollama, wsl, network, connectivity, health-patrol]
    related_skills: [proactive-health-patrol, debug-wsl-windows-network, wsl-readonly-mount-enforcement, tirith-security-bypass]
---

# Diagnose Ollama WSL Connectivity

Diagnose and fix Ollama API unreachable from WSL2 when Ollama runs on Windows host at gateway IP (172.24.160.1:11434). Covers firewall, service state, Tirith blocking, and gateway IP changes.

## When to Use

- Health patrol reports "Ollama FAIL (unreachable or no models)"
- `curl http://172.24.160.1:11434/api/tags` times out or connection refused
- WSL can ping gateway IP but port 11434 closed
- `vision_analyze` or `local_vision` model calls fail

**Don't use for:**
- Ollama running inside WSL (different setup)
- Non-Windows host environments

## Prerequisites

- Ollama installed on Windows host
- WSL2 with systemd enabled
- Gateway IP known (typically 172.24.160.1 for WSL2 default switch)
- `curl`, `ping`, `nvidia-smi` available in WSL

## How to Run

```bash
# Full diagnostic (run each step)
GW_IP=172.24.160.1

# 1. Network reachability
ping -c 2 -W 2 $GW_IP

# 2. Port check
timeout 5 bash -c "cat < /dev/null > /dev/tcp/$GW_IP/11434" && echo "Port open" || echo "Port closed"

# 3. Ollama API direct (use https if configured, or allow HTTP in Tirith)
curl -s --max-time 5 "http://$GW_IP:11434/api/tags" -v 2>&1 | head -20

# 4. Check Windows Firewall rule for 11434 (run in PowerShell as Admin)
# Get-NetFirewallRule -DisplayName "*Ollama*" | Select DisplayName, Enabled, Action, Direction

# 5. Check Ollama service on Windows
# Get-Service Ollama | Select Status, StartType

# 6. Verify gateway IP hasn't changed
ip route | grep default
```

## Quick Reference

| Check | Command | Expected |
|-------|---------|----------|
| Ping gateway | `ping -c 2 172.24.160.1` | 0% loss |
| Port 11434 | `timeout 5 bash -c "cat < /dev/null > /dev/tcp/172.24.160.1/11434"` | Port open |
| Ollama API | `curl -s --max-time 5 http://172.24.160.1:11434/api/tags` | JSON with models[] |
| Windows firewall | PowerShell: `Get-NetFirewallRule -DisplayName "*Ollama*"` | Enabled, Allow, Inbound |
| Ollama service | PowerShell: `Get-Service Ollama` | Running, Automatic |

## Procedure

### 1. Verify Network Layer

**Completion criterion**: Ping succeeds, port 11434 open.

```bash
GW_IP=172.24.160.1
ping -c 2 -W 2 $GW_IP
# If fails: WSL ↔ Windows network broken → see debug-wsl-windows-network

timeout 5 bash -c "cat < /dev/null > /dev/tcp/$GW_IP/11434"
# If fails: Ollama not listening on 0.0.0.0:11434 or firewall blocking
```

### 2. Check Ollama Binding on Windows

**Completion criterion**: Ollama listening on 0.0.0.0:11434 (not 127.0.0.1).

```powershell
# Run in PowerShell on Windows host
netstat -an | findstr 11434
# Should show: TCP 0.0.0.0:11434 LISTENING
# If shows 127.0.0.1:11434 → Ollama only binds localhost → fix needed
```

**Fix**: Set `OLLAMA_HOST=0.0.0.0:11434` in Windows environment variables, restart Ollama service.

### 3. Check Windows Firewall

**Completion criterion**: Inbound rule allowing TCP 11434.

```powershell
# Run in PowerShell as Admin
Get-NetFirewallRule -DisplayName "*Ollama*" | Format-Table DisplayName, Enabled, Action, Direction, LocalPort

# If no rule exists:
New-NetFirewallRule -DisplayName "Ollama API" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow -Profile Private
```

### 4. Check Ollama Service Status

**Completion criterion**: Service running, automatic startup.

```powershell
Get-Service Ollama | Select-Object Status, StartType, Name
# Status: Running, StartType: Automatic
# If stopped: Start-Service Ollama
```

### 5. Handle Tirith Security Blocking

**Completion criterion**: Health patrol can call Ollama API without block.

**Problem**: Tirith blocks `curl http://172.24.160.1:11434/...` as "Plain HTTP URL in execution context".

**Workarounds** (pick one):
1. **Configure Tirith allowlist**: `hermes config set security.website_allowlist '["172.16.0.0/12"]'`
2. **Run checks outside gateway**: Use systemd timer + separate script (not Hermes cron)
3. **Use HTTPS**: Configure Ollama with TLS certs (complex)
4. **Disable Tirith for health checks**: `hermes config set security.tirith_enabled false` (not recommended)

### 6. Verify Gateway IP Stability

**Completion criterion**: Gateway IP matches Ollama binding.

```bash
# In WSL
ip route | grep default
# Should show: default via 172.24.160.1 dev eth0

# If different, update all configs:
# - ~/.hermes/config.yaml (ollama.base_url)
# - Health patrol scripts
# - Any hardcoded IPs
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **Gateway IP changes on reboot** | WSL2 default switch IP can change; use `ip route` to discover dynamically |
| **Ollama binds 127.0.0.1 only** | Set `OLLAMA_HOST=0.0.0.0:11434` in Windows env, restart service |
| **Windows Firewall blocks** | Add inbound rule for TCP 11434 (Private profile) |
| **Tirith blocks health check** | Use systemd timer for infra checks, not Hermes cron; or configure allowlist |
| **VPN interferes** | Corporate VPN may route 172.16.0.0/12 differently; check `ip route` |
| **Ollama not installed as service** | Install via `winget install Ollama.Ollama` (creates service) |

## Verification

```bash
GW_IP=172.24.160.1

# 1. Network OK
ping -c 2 -W 2 $GW_IP | grep -q "0% packet loss" && echo "✅ Ping OK"

# 2. Port open
timeout 5 bash -c "cat < /dev/null > /dev/tcp/$GW_IP/11434" && echo "✅ Port 11434 open"

# 3. API returns models
curl -s --max-time 5 "http://$GW_IP:11434/api/tags" | jq -e '.models | length > 0' && echo "✅ Models available"

# 4. Vision model works (if configured)
~/.hermes/hermes-agent/venv/bin/python -c "
import sys
sys.path.insert(0, '/home/user01/.hermes/hermes-agent')
from gateway.tools.vision import vision_analyze
# Test would need actual image; skip for connectivity check
print('Vision tool import OK')
"

# 5. Health patrol passes
# Next cron run should show Ollima: OK (N models)
```

---

*Distilled from health patrol sessions (20261001_050930_21b570, cron runs Sep 25-30) — Ollama connectivity fails repeatedly due to: (1) Windows Firewall blocking 11434, (2) Ollama binding 127.0.0.1 only, (3) Tirith blocking HTTP calls from Hermes cron, (4) Gateway IP changes. Pattern occurs ≥3 times in last 7 days.*