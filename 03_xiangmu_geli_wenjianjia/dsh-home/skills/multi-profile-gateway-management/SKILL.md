---
name: multi-profile-gateway-management
description: Manage dual Hermes gateway profiles with shared memory.
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [gateway, multi-profile, feishu, scope-recall, systemd]
    related_skills: [configure-feishu-gateway, configure-hermes-memory-provider, configure-messaging-gateway]
---

# Multi-Profile Gateway Management

Manage multiple Hermes gateway profiles (default + empress) running as systemd user services with shared Scope Recall memory, Feishu WebSocket integration, and automatic conflict resolution for writer leases and port collisions.

## When to Use

- Running multiple Hermes profiles simultaneously (e.g., default + empress)
- Shared Scope Recall SQLite database across profiles
- Feishu WebSocket gateway per profile with distinct App IDs
- Scope Recall vector generation with writer lease coordination
- Systemd service management for multi-profile deployments

Don't use for:
- Single-profile setups (use `configure-messaging-gateway` instead)
- Non-Feishu messaging platforms
- Gateway debugging without profile isolation

## Prerequisites

- Hermes installed in each profile: `~/.hermes/` and `~/.hermes/profiles/empress/`
- systemd user services enabled: `systemctl --user daemon-reload`
- Ollama accessible at `172.24.160.1:11434` (Windows host)
- Scope Recall SQLite at shared path: `/home/user01/.hermes/scope-recall/memory.db`
- Feishu App IDs configured per profile (different App IDs for each)
- ChromaDB server on `127.0.0.1:8000` for vector fallback

## How to Run

```bash
# Check status of both gateways
systemctl --user status hermes-gateway hermes-gateway-empress

# Start/stop/restart individual profiles
systemctl --user start hermes-gateway
systemctl --user restart hermes-gateway-empress

# View logs for debugging
journalctl --user -u hermes-gateway -f
journalctl --user -u hermes-gateway-empress -f

# Sync Scope Recall config between profiles
cp ~/.hermes/scope-recall/config.json ~/.hermes/profiles/empress/scope-recall/config.json
mkdir -p ~/.hermes/profiles/empress/scope-recall/
```

## Quick Reference

| Task | Command |
|------|---------|
| List all hermes units | `systemctl --user list-units 'hermes*'` |
| List timers | `systemctl --user list-timers 'hermes*'` |
| Gateway logs (default) | `journalctl --user -u hermes-gateway -n 100` |
| Gateway logs (empress) | `journalctl --user -u hermes-gateway-empress -n 100` |
| Restart both | `systemctl --user restart hermes-gateway hermes-gateway-empress` |
| Scope Recall config sync | `cp ~/.hermes/scope-recall/config.json ~/.hermes/profiles/empress/scope-recall/` |
| Vector generation | `hermes scope-recall vector generate --apply --profile empress` |

## Procedure

### 1. Verify Service Definitions

**Completion criterion**: Both service files exist with correct `HERMES_HOME` and `EnvironmentFile`.

```bash
# Check service files
cat ~/.config/systemd/user/hermes-gateway.service
cat ~/.config/systemd/user/hermes-gateway-empress.service

# Key differences:
# hermes-gateway:     HERMES_HOME=/home/user01/.hermes
# hermes-gateway-empress: HERMES_HOME=/home/user01/.hermes/profiles/empress
```

### 2. Validate Feishu App ID Isolation

**Completion criterion**: Each profile uses distinct Feishu App ID in `.env`.

```bash
# Check .env files
cat ~/.hermes/.env | grep FEISHU
cat ~/.hermes/profiles/empress/.env | grep FEISHU

# Must differ:
# default:    FEISHU_APP_ID=cli_xxx_default
# empress:    FEISHU_APP_ID=cli_xxx_empress
```

### 3. Sync Scope Recall Configuration

**Completion criterion**: Both profiles have identical `config.json` with SQLite path and vector settings.

```json
// ~/.hermes/scope-recall/config.json (source)
{
  "storage": "sqlite",
  "sqlite_path": "/home/user01/.hermes/scope-recall/memory.db",
  "vector": {
    "enabled": true,
    "provider": "lancedb",
    "path": "/home/user01/.hermes/scope-recall/vectors"
  }
}

// Copy to empress profile
cp ~/.hermes/scope-recall/config.json ~/.hermes/profiles/empress/scope-recall/config.json
```

### 4. Coordinate Vector Generation (Writer Lease)

**Completion criterion**: Vector generation runs on one profile at a time; other uses read-only.

```bash
# Stop both gateways before vector generation
systemctl --user stop hermes-gateway hermes-gateway-empress

# Generate vectors on default profile (holds writer lease)
HERMES_HOME=/home/user01/.hermes hermes scope-recall vector generate --apply

# Activate existing vectors on empress (reader mode)
HERMES_HOME=/home/user01/.hermes/profiles/empress hermes scope-recall vector activate-existing-ready

# Restart both gateways
systemctl --user start hermes-gateway hermes-gateway-empress
```

### 5. Health Verification

**Completion criterion**: Both gateways respond; memory queries work on both profiles.

```bash
# Test default profile
HERMES_HOME=/home/user01/.hermes hermes memory stats

# Test empress profile
HERMES_HOME=/home/user01/.hermes/profiles/empress hermes memory stats

# Feishu message test: send to each bot, verify response
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| Both gateways bind same port | Each service must use different port (default: 8080, empress: 8081) |
| Feishu webhook conflict | Distinct App IDs per profile; verify `FEISHU_APP_ID` in each `.env` |
| Scope Recall writer lease contention | Stop gateways before vector generation; use `--activate-existing-ready` for readers |
| Vector fallback to lancedb | Ensure `config.json` has `vector.enabled: true` and valid `lancedb` path |
| Profile config drift | Sync `config.json` after any Scope Recall schema change |
| Cron timers only in default | Timers defined in default profile only; empress inherits via shared DB |

## Verification

```bash
# 1. Both services active
systemctl --user is-active hermes-gateway hermes-gateway-empress
# Expected: active, active

# 2. Distinct ports listening
ss -ltnp | grep -E '8080|8081'
# Expected: python on 8080 (default), python on 8081 (empress)

# 3. Shared DB accessible
sqlite3 /home/user01/.hermes/scope-recall/memory.db "SELECT COUNT(*) FROM memories;"

# 4. Vector index exists
ls -la /home/user01/.hermes/scope-recall/vectors/

# 5. Feishu connectivity
curl -s -X POST "https://open.feishu.cn/open-apis/bot/v2/hook/<DEFAULT_WEBHOOK>" -d '{"msg_type":"text","content":{"text":"test default"}}'
curl -s -X POST "https://open.feishu.cn/open-apis/bot/v2/hook/<EMPRESS_WEBHOOK>" -d '{"msg_type":"text","content":{"text":"test empress"}}'
```

---

*Distilled from sessions 20260908_042140_65b6a3aa, 20260911_215130_276e7d88, cron_d18ba14f7b08_20260911_180428, cron_d18ba14f7b08_20260922_173940 (Sep 8-22, 2026). Pattern threshold ≥3 met across: dual gateway services, Scope Recall config sync, Feishu App ID isolation, writer lease coordination, vector fallback to lancedb.*