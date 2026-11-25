---
name: configure-systemd-timeouts
description: "Set systemd timeouts for long-running Hermes services."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - systemd
    - timeout
    - service-config
    - wsl
    - long-running
    related_skills:
    - manage-systemd-services-wsl
    - fix-systemd-hardcoded-paths
    - proactive-health-patrol
    - wsl-hermes-system-health
---

# Configure systemd Service Timeouts

Configure `TimeoutStartSec`, `TimeoutStopSec`, and `TimeoutSec` in systemd user service units or drop-ins for long-running Hermes services that exceed the default 90-second timeout. Prevents false "failed" status for services like `uumit-cruise-status`, `master-money-maker`, and health patrol jobs.

## When to Use

- Service shows `loaded failed failed` but manual execution succeeds
- Health patrol reports systemd service failures for long-running tasks
- Network-dependent services (API calls, web scraping) that may take >90s
- Cron-triggered services that do batch processing
- Any service where `journalctl` shows timeout-related messages

**Don't use for:** Quick services (gateways, daemons that start in <10s), system-level services (requires sudo).

## Prerequisites

- WSL2 with `systemd=true` in `/etc/wsl.conf`
- `systemctl --user` access
- Service unit file at `~/.config/systemd/user/<name>.service`
- Drop-in directory `~/.config/systemd/user/<name>.service.d/` for non-destructive overrides

## How to Run

```bash
# Quick fix via drop-in (recommended, non-destructive)
mkdir -p ~/.config/systemd/user/<service>.service.d
cat > ~/.config/systemd/user/<service>.service.d/timeout.conf <<'EOF'
[Service]
TimeoutStartSec=300
TimeoutStopSec=120
TimeoutSec=300
EOF
systemctl --user daemon-reload
systemctl --user restart <service>
```

## Quick Reference

| Task | Command |
|------|---------|
| Check current timeouts | `systemctl --user show <service> -p TimeoutStartUSec,TimeoutStopUSec,TimeoutSec` |
| Create drop-in timeout | `mkdir -p ~/.config/systemd/user/<svc>.service.d && cat > .../timeout.conf` |
| Reload daemon | `systemctl --user daemon-reload` |
| Restart service | `systemctl --user restart <service>` |
| Verify active | `systemctl --user status <service> --no-pager` |
| List all user services | `systemctl --user list-units --state=failed --no-pager` |

## Procedure

### 1. Identify Services Needing Timeout Increases

```bash
# List failed user services
systemctl --user list-units --state=failed --no-pager

# Check timeout settings for a specific service
systemctl --user show uumit-cruise-status.service -p TimeoutStartUSec,TimeoutStopUSec,TimeoutSec
```

**Completion criterion:** List of services with default 90s timeout that fail due to legitimate long execution.

### 2. Determine Appropriate Timeout Values

| Service Type | TimeoutStartSec | TimeoutStopSec | Rationale |
|--------------|----------------|----------------|-----------|
| Network API polling (uumit-cruise-status) | 300 (5 min) | 60 | API latency + retries |
| Master money maker loop | 600 (10 min) | 120 | Multi-platform batch |
| Health patrol (7 checks) | 180 (3 min) | 60 | Sequential network calls |
| Novel pipeline steps | 600 (10 min) | 120 | LLM generation + review |
| CUA driver automation | 300 (5 min) | 60 | Browser/page interactions |

**Default systemd values:** `TimeoutStartSec=90`, `TimeoutStopSec=90`, `TimeoutSec=90`

**Completion criterion:** Timeout values assigned per service with rationale documented.

### 3. Create Drop-in Timeout Configuration (Recommended)

```bash
# For each service needing timeout increase:
SVC="uumit-cruise-status"
mkdir -p ~/.config/systemd/user/${SVC}.service.d
cat > ~/.config/systemd/user/${SVC}.service.d/timeout.conf <<'EOF'
[Service]
TimeoutStartSec=300
TimeoutStopSec=60
TimeoutSec=300
EOF

# Repeat for other services...
SVC="master-money-maker"
mkdir -p ~/.config/systemd/user/${SVC}.service.d
cat > ~/.config/systemd/user/${SVC}.service.d/timeout.conf <<'EOF'
[Service]
TimeoutStartSec=600
TimeoutStopSec=120
TimeoutSec=600
EOF
```

**Completion criterion:** Drop-in files created for all target services with appropriate timeouts.

### 4. Alternative: Edit Service Unit Directly

```bash
# Only if drop-in not suitable (rare)
systemctl --user edit --full <service>
# Add to [Service] section:
# TimeoutStartSec=300
# TimeoutStopSec=60
# TimeoutSec=300
```

**Completion criterion:** Unit file updated with timeout settings.

### 5. Reload and Verify

```bash
# Reload systemd to pick up drop-ins
systemctl --user daemon-reload

# Restart each service
for svc in uumit-cruise-status master-money-maker; do
    systemctl --user restart "$svc"
done

# Verify timeouts applied
for svc in uumit-cruise-status master-money-maker; do
    echo "=== $svc ==="
    systemctl --user show "$svc" -p TimeoutStartUSec,TimeoutStopUSec,TimeoutSec
    systemctl --user status "$svc" --no-pager | head -5
done
```

**Completion criterion:** All services show `Active: active (running)` and timeout values match configuration.

### 6. Validate with Health Patrol

```bash
# Run proactive patrol to confirm no timeout failures
python3 /home/user01/.hermes/scripts/proactive_patrol.py --check systemd

# Or full patrol
python3 /home/user01/.hermes/scripts/proactive_patrol.py
```

**Completion criterion:** Health patrol reports no systemd service timeout failures.

## Pitfalls

| Issue | Solution |
|-------|----------|
| Drop-in not taking effect | Ensure `daemon-reload` after creating drop-in; check `systemctl --user show <svc> -p DropInPaths` |
| Service still fails after timeout increase | Check actual execution time with `journalctl -u <svc> -o short-precise`; may need even longer timeout or code optimization |
| TimeoutSec vs TimeoutStartSec | `TimeoutStartSec` = start phase only; `TimeoutSec` = overall (start + running + stop). Set both. |
| Unit file overrides drop-in | Drop-ins have higher priority for same keys. Verify with `systemctl --user cat <service>` |
| `TimeoutStartUSec` shown in microseconds | `systemctl show` displays microseconds; 300s = 300000000. Config uses seconds. |
| Service type `oneshot` vs `exec` | `oneshot` services use `TimeoutSec` for entire execution. `exec`/`simple` use `TimeoutStartSec` for startup. |

## Verification

```bash
# 1. No failed services due to timeout
systemctl --user list-units --state=failed --no-pager | grep -v timeout && echo "✅ No timeout failures"

# 2. All target services show custom timeouts
for svc in uumit-cruise-status master-money-maker; do
    start=$(systemctl --user show "$svc" -p TimeoutStartUSec --value)
    stop=$(systemctl --user show "$svc" -p TimeoutStopUSec --value)
    [[ $start -gt 90000000 ]] && echo "✅ $svc TimeoutStartSec: $((start/1000000))s" || echo "❌ $svc TimeoutStartSec still default"
    [[ $stop -gt 90000000 ]] && echo "✅ $svc TimeoutStopSec: $((stop/1000000))s" || echo "❌ $svc TimeoutStopSec still default"
done

# 3. Services survive actual runs (wait for next cron cycle or trigger manually)
systemctl --user start uumit-cruise-status
sleep 5
systemctl --user status uumit-cruise-status --no-pager | grep -q "active" && echo "✅ Service started successfully"
```

---

*Skill distilled from 3+ incidents (Oct 7-9, 2026): uumit-cruise-status.service repeatedly failed with default 90s timeout despite manual execution succeeding in ~120s; master-money-maker and health patrol services at risk. Pattern: network-dependent cron services exceed default timeout, require explicit timeout configuration via drop-ins.*