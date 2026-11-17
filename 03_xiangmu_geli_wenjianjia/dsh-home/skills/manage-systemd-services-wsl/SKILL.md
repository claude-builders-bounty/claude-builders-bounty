---
name: manage-systemd-services-wsl
description: "Use when you need to install, start, stop, restart, enable, disable, or debug systemd user services in WSL2. Covers service files, drop-ins, timers, logs. Do NOT use for system-level services (requires sudo)."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms:
- linux
- windows
metadata:
  hermes:
    tags:
    - systemd
    - wsl
    - services
    - gateway
    - cron
    related_skills:
    - verify-hermes-setup
    - edit-config-files-wsl
    requires_toolsets:
    - terminal
---




# Manage systemd Services in WSL

Install, enable, start, and debug systemd user services in WSL2 (requires systemd enabled in `/etc/wsl.conf`).

## When to Use

- Run long-lived daemons: `hermes-gateway`, custom services
- Schedule cron jobs via systemd timers
- Debug service failures with `journalctl`
- WSL2 with `systemd=true` in `/etc/wsl.conf`

## Prerequisites

- WSL2 with `systemd=true` in `/etc/wsl.conf` + `wsl --shutdown` restart
- `loginctl enable-linger $USER` for user services to survive logout
- Service unit file at `~/.config/systemd/user/<name>.service`

## How to Run

```bash
# Install service unit
mkdir -p ~/.config/systemd/user
cp /path/to/service.service ~/.config/systemd/user/

# Enable + start
systemctl --user daemon-reload
systemctl --user enable --now service-name

# Check status
systemctl --user status service-name

# View logs
journalctl --user -u service-name -n 50 --no-pager
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `systemctl --user daemon-reload` | Reload unit files |
| `systemctl --user enable --now name` | Enable + start immediately |
| `systemctl --user status name` | Current state |
| `systemctl --user restart name` | Restart |
| `systemctl --user stop name` | Stop |
| `journalctl --user -u name -f` | Follow logs |
| `loginctl enable-linger $USER` | Persist user services |

## Procedure

### 1. Verify systemd Is Running

```bash
systemctl --user status
# Should show "State: running" or similar, not "Failed to connect to bus"
```

**If failed**: Check `/etc/wsl.conf` has `[boot]\nsystemd=true`, then `wsl --shutdown` in PowerShell and restart WSL.

### 2. Enable Linger (Once Per User)

```bash
loginctl enable-linger $USER
```

**Success criterion:** No error; `loginctl show-user $USER | grep Linger` shows `Linger=yes`.

### 3. Create Service Unit File

**Template for Hermes Gateway:**
```ini
# ~/.config/systemd/user/hermes-gateway.service
[Unit]
Description=Hermes Agent Gateway - Messaging Platform Integration
After=network.target

[Service]
Type=exec
ExecStart=/home/user/.hermes/hermes-agent/venv/bin/hermes gateway run
WorkingDirectory=/home/user/.hermes/hermes-agent
Restart=on-failure
RestartSec=5
Environment=PATH=/home/user/.hermes/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
```

### 4. Install and Start

```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-gateway
```

**Success criterion:** `systemctl --user status hermes-gateway` shows `Active: active (running)`.

### 5. Debug Failures

```bash
# Recent logs
journalctl --user -u hermes-gateway -n 50 --no-pager

# Follow live
journalctl --user -u hermes-gateway -f

# Check exit code
systemctl --user status hermes-gateway | grep -E "(Active:|Main PID:|Exit)"
```

**Common failures:**
- `ExecStart` path wrong → fix path in unit file, `daemon-reload`, `restart`
- Missing venv → ensure venv exists at path in `ExecStart`
- Port conflict → check `ss -tlnp | grep :PORT`

## Pitfalls

- **systemd not running**: WSL default is no systemd. Must edit `/etc/wsl.conf` + restart WSL.
- **User services die on logout**: `loginctl enable-linger $USER` fixes this.
- **PATH in service**: Systemd user services don't inherit shell PATH. Set `Environment=PATH=...` in unit.
- **Venv python path**: Use full path `/home/user/.hermes/hermes-agent/venv/bin/hermes`, not just `hermes`.
- **Journalctl output truncated**: Use `--no-pager -n 100` for full view.
- **OpenClaw gateway service** — requires Node.js with heap config:
  ```ini
  # ~/.config/systemd/user/openclaw-gateway.service
  [Unit]
  Description=OpenClaw Gateway
  After=network.target

  [Service]
  Type=exec
  ExecStart=/usr/bin/node --max-old-space-size=8192 /home/user/.openclaw/tools/node-v24.19.0/lib/node_modules/openclaw/dist/index.js gateway --port 18789
  WorkingDirectory=/home/user
  Restart=on-failure
  RestartSec=5
  Environment=PATH=/home/user/.openclaw/tools/node-v24.19.0/bin:/usr/local/bin:/usr/bin:/bin
  Environment=OPENCLAW_GATEWAY_PORT=18789

  [Install]
  WantedBy=default.target
  ```
- **Node.js path stability** — `/tmp/node-vX/` not persistent; use nvm/apt stable path like `/usr/bin/node` or `~/.nvm/versions/node/vX/bin/node`.

## Verification

1. `systemctl --user is-active hermes-gateway` → `active`
2. `journalctl --user -u hermes-gateway -n 5 --no-pager` → shows startup messages
3. Service survives: close terminal, reopen WSL, `systemctl --user status hermes-gateway` still `active`

---

*Skill generated from session pattern analysis (manage-systemd-services-wsl appeared in 3+ sessions).*