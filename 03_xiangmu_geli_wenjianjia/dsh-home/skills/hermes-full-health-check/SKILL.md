---
name: hermes-full-health-check
description: "Use when you need comprehensive 8-layer system audit (config, skills, memory, scheduling, gateway, scripts, security, noise) with P0/P1/P2 fixes and verification commands. Outputs JSON report. Do NOT use for quick health checks."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms:
- linux
- windows
metadata:
  hermes:
    tags:
    - health-check
    - diagnostics
    - hermes-agent
    - system-audit
    - json-report
    related_skills:
    - verify-hermes-setup
    - proactive-health-patrol
    - troubleshoot-hermes-config
    - configure-feishu-gateway
    - manage-systemd-services-wsl
    requires_toolsets:
    - terminal
    - file
---




# Hermes Full Health Check

Run a comprehensive system health check across all Hermes layers (core config, skills, memory, scheduling, gateway, scripts, security, noise) and generate a structured JSON report with P0/P1/P2 priority fixes.

## When to Use

- Weekly/monthly system audit
- After major config changes or upgrades
- When experiencing unexplained failures or degraded performance
- Before/after migrating profiles or environments
- **Post-migration audit: verify Windows ↔ WSL2 config sync, ChromaDB path accuracy, cron model pinning**
- User requests "full health check" or "system audit"

## Prerequisites

- Hermes CLI functional (`hermes config show` works)
- Access to `~/.hermes/` directory
- systemd user services accessible (`systemctl --user`)
- Python 3.10+ with chromadb importable
- `jq` for JSON processing (optional, for pretty output)

## How to Run

```bash
# Full check with JSON output
hermes skill run hermes-full-health-check --output json > health_report.json

# Human-readable summary
hermes skill run hermes-full-health-check --output summary

# Quick check (skip slow layers)
hermes skill run hermes-full-health-check --quick
```

## Quick Reference

| Task | Command |
|------|---------|
| Full JSON report | `hermes skill run hermes-full-health-check --output json` |
| Summary only | `hermes skill run hermes-full-health-check --output summary` |
| Quick mode | `hermes skill run hermes-full-health-check --quick` |
| Save to file | `hermes skill run hermes-full-health-check --output json > report.json` |
| **Dual-env sync check** | `diff -u /mnt/d/Ai/Agent/hermes/SOUL.md /home/user01/.hermes/SOUL.md` (repeat for USER.md, MEMORY.md, config.yaml) |
| **Cron drift check** | `cat ~/.hermes/cron/jobs.json | jq -r '.jobs[] | select(.name=="auto-skill-distill") | .model_snapshot, .provider_snapshot'` |
| **Guard test** | `python3 -c "import sys; sys.path.insert(0, '~/.hermes/python'); import tools.guard"` |

## Procedure

### 1. Layer 1: Core Config & Models
```bash
# Check config exists and parns
hermes config show >/dev/null && echo "PASS" || echo "FAIL"

# Verify primary model configured
hermes config get model.default

# Verify vision model configured
hermes config get model.auxiliary.vision

# Check NVIDIA auth
ls -la ~/.hermes/auth.json
```

**Completion criterion:** All model config present, auth.json has valid NVIDIA key (env source preferred).

### 2. Layer 2: Skills System
```bash
# Count enabled skills
hermes skills list --enabled-only | wc -l

# Check for [SKILL_PRUNED] markers
grep -r "SKILL_PRUNED" ~/.hermes/skills/ 2>/dev/null | wc -l

# Verify core custom skills load
hermes skill view proactive-hermes >/dev/null && echo "PASS" || echo "FAIL"
hermes skill view learning-capture >/dev/null && echo "PASS" || echo "FAIL"
```

**Completion criterion:** Skills load without error, minimal pruned markers, reasonable enabled count (<50).

### 3. Layer 3: Memory System (Scope Recall + ChromaDB)
```bash
# Check Scope Recall DB exists
ls -la ~/.hermes/memory/scope_recall.db

# Check tables
sqlite3 ~/.hermes/memory/scope_recall.db ".tables" | grep -E "memory|user|project|ops|preference|fact"

# Check ChromaDB collections
python3 -c "import chromadb; c=chromadb.PersistentClient('/home/user01/.hermes/chroma'); print(len(c.list_collections()))"

# Check embedder config
grep -E "SCOPE_RECALL.*EMBEDDING|embed_model" ~/.hermes/.env ~/.hermes/config.yaml 2>/dev/null
```

**Completion criterion:** SQLite DB exists with 6 tables, ChromaDB has ≥1 collection, embedder configured.

### 4. Layer 4: Scheduling (Systemd + Cron)
```bash
# List hermes timers
systemctl --user list-timers 'hermes*' --no-pager

# Check critical timers exist
systemctl --user list-timers | grep -E "compress|distill|health" || echo "MISSING"

# Check gateway services
systemctl --user list-units 'hermes*gateway*' --no-pager
```

**Completion criterion:** Timers for daily compression (03:00), skill distillation (04:00), health patrol present and enabled.

### 5. Layer 5: Gateway / Feishu
```bash
# Check Feishu platform enabled
hermes config get platform.feishu.enabled

# Check credentials in .env (not config.yaml)
grep FEISHU ~/.hermes/.env

# Check gateway logs for connectivity
journalctl --user -u hermes-gateway -n 50 --no-pager | grep -E "Connected|feishu|ERROR"
```

**Completion criterion:** Feishu connected, secrets in .env, no persistent errors.

### 6. Layer 6: Script Library Safety
```bash
# Check guard.py exists
ls -la /home/user01/.hermes/python/tools/guard.py

# Check utility modules
ls -la /home/user01/.hermes/python/tools/fs.py /home/user01/.hermes/python/tools/proc.py /home/user01/.hermes/python/tools/jsonio.py 2>/dev/null

# Check deploy script
ls -la /home/user01/.hermes/python/deploy_to_prod.sh

# Check wsl.conf readonly
grep -A2 "automount" /etc/wsl.conf | grep "ro,noatime" || echo "NOT RO"
```

**Completion criterion:** guard.py + utilities + deploy script present, /mnt/c/d mounted readonly.

### 7. Layer 7: Security Vulnerabilities
```bash
# Check for hardcoded NVIDIA key in auth.json
grep -r "nvapi-" ~/.hermes/auth.json && echo "HARDCODED FOUND" || echo "CLEAN"

# Check Feishu secret in config.yaml vs .env
hermes config get platform.feishu.app_secret | grep -E "^\$\{.*\}$" && echo "IN ENV" || echo "IN CONFIG"

# Check mount permissions
mount | grep "/mnt/c\|/mnt/d" | grep "rw," && echo "RW MOUNT" || echo "RO MOUNT"
```

**Completion criterion:** No hardcoded secrets, all secrets via env vars, Windows mounts readonly.

### 8. Layer 8: Noise / Pollution
```bash
# Check for PoE2 projects in script dir
ls /home/user01/.hermes/python/ | grep -E "poe2|agent-of-exile" | wc -l

# Check session dump accumulation
find ~/.hermes/sessions -name "request_dump_*.json" -mtime +7 | wc -l
```

**Completion criterion:** Script dir clean of project-specific code, old request dumps cleaned.

### 9. Layer 9: Dual-Environment Sync & Migration Verification
```bash
# Ensure WSL is running
wsl -d Ubuntu-24.04 -- echo "WSL up" || wsl --start Ubuntu-24.04

# Diff critical config files between Windows and WSL
for f in config.yaml SOUL.md USER.md MEMORY.md; do
  diff -u /mnt/d/Ai/Agent/hermes/$f /home/user01/.hermes/$f 2>/dev/null || echo "MISSING OR DIVERGED: $f"
done

# Diff memories/ directory
for f in USER.md MEMORY.md; do
  diff -u /mnt/d/Ai/Agent/hermes/memories/$f /home/user01/.hermes/memories/$f 2>/dev/null || echo "MISSING OR DIVERGED: memories/$f"
done

# Verify ChromaDB physical location matches documentation
grep -r "chroma" /mnt/d/Ai/Agent/hermes/MEMORY.md /home/user01/.hermes/MEMORY.md 2>/dev/null
ls -la /home/user01/.hermes/chroma/
# Windows path (if documented) should exist or be symlinked
[ -d /mnt/d/Ai/Ollama/Memory/chroma ] || echo "WARN: Documented Windows ChromaDB path missing"

# Check cron job model pinning
cat /home/user01/.hermes/cron/jobs.json | jq -r '.jobs[] | select(.name=="auto-skill-distill") | .model_snapshot, .provider_snapshot'

# Verify Guard enforcement
test -f /home/user01/.hermes/python/tools/guard.py && python3 -c "import sys; sys.path.insert(0, '/home/user01/.hermes/python'); import tools.guard; print('Guard OK')"
```

**Completion criterion:** All critical configs synced (or intentional divergence documented), ChromaDB path accurate, cron jobs pinned to correct model, Guard enforcement active.

## Pitfalls

- **ChromaDB venv issue**: systemd services may not activate venv → run chromadb check from user shell
- **Scope Recall writer lease**: Gateway holds DB lock → stop gateway briefly for migration activation
- **Skill loader cache**: New skills not visible until next session
- **Timer precision**: systemd timers may drift; check `systemctl --user list-timers` for next elapsed
- **Dual-environment config drift**: Windows (`D:\Ai\Agent\hermes\`) and WSL2 (`/home/user01/.hermes/`) maintain separate copies of SOUL.md, USER.md, MEMORY.md — they diverge silently. Always diff both sides during audit.
- **ChromaDB path mismatch**: Documentation (MEMORY.md) may reference stale Windows path (`D:/Ai/Ollama/Memory/chroma`) while actual DB lives at `~/.hermes/chroma/`. Verify physical location vs documented location.
- **Cron job model drift**: `auto-skill-distill` and similar jobs skip with "drift_skip" when global inference config changes. Must explicitly pin model/provider in cron job or restore original config.
- **WSL stopped state**: WSL2 may be Stopped; `systemctl --user`, cron, and Ollama connectivity all fail. Start WSL first: `wsl -d Ubuntu-24.04`.
- **Guard.py mount enforcement**: `/etc/wsl.conf` readonly mount is kernel-enforced; guard.py adds userspace check. Both must pass — verify with `mount | grep /mnt/c` and guard import test.

## Verification

```bash
# 1. JSON report generated and valid
python3 -m json.tool health_report.json >/dev/null && echo "Valid JSON"

# 2. All 9 layers present in report
jq '.layers | keys' health_report.json

# 3. P0 issues count
jq '.priority_fixes[0].issues | length' health_report.json

# 4. Verification commands from report work
# (Run the commands listed in report.verification_commands.after_fixes_run)

# 5. Dual-env sync: no unintended diffs
diff -u /mnt/d/Ai/Agent/hermes/config.yaml /home/user01/.hermes/config.yaml && echo "config.yaml SYNC"
diff -u /mnt/d/Ai/Agent/hermes/SOUL.md /home/user01/.hermes/SOUL.md && echo "SOUL.md SYNC"
diff -u /mnt/d/Ai/Agent/hermes/USER.md /home/user01/.hermes/USER.md && echo "USER.md SYNC"
# MEMORY.md may intentionally differ (WSL has Scope Recall detail, Windows has ChromaDB detail)
```

---

*Skill distilled from session 20260908_042140_65b6a3aa (comprehensive health check with 42 checks across 8 layers, 10 P0 issues identified). Pattern threshold met via recurring diagnostic need across multiple sessions.*