---
name: verify-hermes-setup
description: Run post-install verification checklist for Hermes Agent in WSL.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [verification, checklist, hermes, wsl, health-check]
    related_skills: [install-chromadb-wsl, manage-python-venv-wsl, edit-config-files-wsl, manage-systemd-services-wsl]
---

# Verify Hermes Setup

Comprehensive post-install verification checklist for Hermes Agent in WSL environments. Run after any major setup change to confirm all subsystems work.

## When to Use

- After initial Hermes install or major update
- After configuring memory skills, gateway, or cron jobs
- After WSL restart or systemd changes
- Before starting important work sessions

## Prerequisites

- Hermes installed (CLI works: `hermes --version`)
- WSL2 with systemd enabled (for gateway/cron)
- Project venv active or known path

## How to Run

```bash
# Quick health check (30 sec)
/path/to/venv/bin/python -c "
import hermes; print('Hermes import OK')
import chromadb; print('ChromaDB:', chromadb.__version__)
import ollama; print('Ollama client OK')
"

# Full checklist (2-3 min): run each section below
```

## Quick Reference

| Check | Command | Expected |
|-------|---------|----------|
| Hermes CLI | `hermes --version` | Version printed |
| Python deps | `venv/bin/python -c "import chromadb, ollama"` | No error |
| Config valid | `hermes config get model.provider` | Returns provider |
| Gateway | `systemctl --user status hermes-gateway` | active (running) |
| Cron jobs | `cronjob list` | Shows scheduled jobs |
| Memory skill | `skill_view memory-local` | Skill loads |
| Ollama reachable | `curl -s http://host.docker.internal:11434/api/tags` | JSON with models |

## Procedure

### 1. Core Hermes CLI

```bash
hermes --version
hermes config get model.provider model.base_url
```

✅ **Pass:** Version prints; config shows configured provider (e.g., `nvidia`).

### 2. Python Dependencies (Venv)

```bash
/path/to/venv/bin/python -c "
import chromadb; print('ChromaDB', chromadb.__version__)
import ollama; print('Ollama', ollama.__version__)
import yaml; print('PyYAML OK')
"
```

✅ **Pass:** All imports succeed, versions print.

### 3. Configuration Validity

```bash
# Main config
hermes config get model.provider
hermes config get memory.memory_enabled

# Skill configs (if using memory-local)
cat /home/user/.hermes/skills/memory/memory-local/references/config.yaml | head -30
python3 -c "import yaml; yaml.safe_load(open('/home/user/.hermes/skills/memory/memory-local/references/config.yaml')); print('YAML OK')"
```

✅ **Pass:** All keys return values; YAML parses cleanly.

### 4. Gateway Service (Requires systemd)

```bash
systemctl --user status hermes-gateway
journalctl --user -u hermes-gateway -n 10 --no-pager | grep -E "(Loaded hook|Scheduled)"
```

✅ **Pass:** Service `active (running)`; logs show `[hooks] Loaded hook 'memory-local'` and `[cron] Job memory-local-compression scheduled`.

### 5. Cron Jobs

```bash
cronjob list
```

✅ **Pass:** Shows expected jobs (e.g., `memory-local-compression` at 03:00, `auto-skill-distill` at 04:00) with `enabled: true`.

### 6. Memory System

```bash
# Built-in memory tool
memory action=view

# memory-local skill (if configured)
skill_view memory-local
```

✅ **Pass:** Memory shows usage; skill loads with hooks/cron config.

### 7. Ollama Connectivity (WSL → Windows Host)

```bash
# Test Windows Ollama from WSL
curl -s --max-time 5 http://host.docker.internal:11434/api/tags | jq '.models | length'

# Or with Python
/path/to/venv/bin/python -c "
import ollama
client = ollama.Client(host='http://host.docker.internal:11434')
models = client.list()
print(f'{len(models.models)} models available')
"
```

✅ **Pass:** Returns model count > 0; `bge-m3` present for embeddings.

### 8. GPU/Compute (If Applicable)

```bash
/path/to/venv/bin/python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

✅ **Pass:** CUDA available, GPU name matches hardware.

## Pitfalls

- **Gateway not running**: Memory hooks/cron won't work. Start with `systemctl --user start hermes-gateway`.
- **Ollama on Windows**: Use `host.docker.internal:11434`, NOT `localhost:11434` from WSL.
- **Venv mismatch**: Always use the same venv python that Hermes uses (check `hermes config get` or `which hermes`).
- **systemd not enabled**: Gateway/cron require `/etc/wsl.conf` → `[boot]\nsystemd=true` + WSL restart.
- **Port conflicts**: Gateway default ports may clash; check `ss -tlnp`.

## Verification

**All 8 checks pass** = ✅ Fully operational.

**Partial pass** = Note which failed; re-run corresponding skill:
- 1-2 failed → `manage-python-venv-wsl` + `install-chromadb-wsl`
- 3 failed → `edit-config-files-wsl`
- 4 failed → `manage-systemd-services-wsl`
- 5 failed → check `cronjob` tool / gateway logs
- 6 failed → check skill config + gateway
- 7 failed → Windows Ollama service + firewall + `host.docker.internal`
- 8 failed → CUDA toolkit / PyTorch reinstall

---

*Skill generated from session pattern analysis (verify-hermes-setup appeared in 4+ sessions).*