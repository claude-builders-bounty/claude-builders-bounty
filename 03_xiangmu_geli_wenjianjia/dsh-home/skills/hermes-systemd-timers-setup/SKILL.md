---
name: hermes-systemd-timers-setup
description: "Create systemd timers for Hermes daily jobs."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [systemd, timers, cron, scheduling, automation]
    related_skills: [manage-systemd-services-wsl, proactive-health-patrol, memory-local, auto-skill-distill]
---

# Hermes Systemd Timers Setup

Create and manage systemd user timers for Hermes recurring jobs: daily context compression (03:00), daily skill distillation (04:00), hourly health patrol, and Feishu gateway keepalive (every 4 min).

## When to Use

- Initial Hermes setup on new machine/profile
- After `hermes-full-health-check` reports missing timers
- When adding new recurring maintenance tasks
- Migrating from cron to systemd timers
- Timer drift or missed executions

## Prerequisites

- systemd user instance running (`systemctl --user status`)
- `loginctl enable-linger $USER` for boot persistence
- Hermes gateway service installed (`hermes gateway install`)
- Write access to `~/.config/systemd/user/`

## How to Run

```bash
# Create all standard timers
hermes skill run hermes-systemd-timers-setup --create-all

# Create specific timer
hermes skill run hermes-systemd-timers-setup --create compress
hermes skill run hermes-systemd-timers-setup --create distill
hermes skill run hermes-systemd-timers-setup --create health-patrol

# List current timers
hermes skill run hermes-systemd-timers-setup --list

# Enable and start
hermes skill run hermes-systemd-timers-setup --enable-all
```

## Quick Reference

| Task | Command |
|------|---------|
| Create all timers | `hermes skill run hermes-systemd-timers-setup --create-all` |
| List timers | `hermes skill run hermes-systemd-timers-setup --list` |
| Enable all | `hermes skill run hermes-systemd-timers-setup --enable-all` |
| Check status | `systemctl --user list-timers 'hermes*' --no-pager` |

## Procedure

### 1. Ensure Linger Enabled
```bash
loginctl enable-linger $USER
loginctl show-user $USER | grep Linger
# Should show: Linger=yes
```
**Completion criterion:** Linger=yes (services survive SSH logout).

### 2. Create Daily Compression Timer (03:00)
```bash
cat > ~/.config/systemd/user/hermes-daily-compress.service <<'EOF'
[Unit]
Description=Hermes Daily Context Compression
After=network-online.target

[Service]
Type=oneshot
ExecStart=/home/user01/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main memory compress --all
WorkingDirectory=/home/user01/.hermes
Environment="PATH=/home/user01/.hermes/hermes-agent/venv/bin:/usr/bin:/bin"
Environment="HERMES_HOME=/home/user01/.hermes"
StandardOutput=journal
StandardError=journal
EOF

cat > ~/.config/systemd/user/hermes-daily-compress.timer <<'EOF'
[Unit]
Description=Daily Hermes context compression at 03:00

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
EOF
```
**Completion criterion:** Both `.service` and `.timer` files created.

### 3. Create Daily Skill Distillation Timer (04:00)
```bash
cat > ~/.config/systemd/user/hermes-skill-distill.service <<'EOF'
[Unit]
Description=Hermes Daily Skill Distillation
After=network-online.target

[Service]
Type=oneshot
ExecStart=/home/user01/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main skill distill --days 7
WorkingDirectory=/home/user01/.hermes
Environment="PATH=/home/user01/.hermes/hermes-agent/venv/bin:/usr/bin:/bin"
Environment="HERMES_HOME=/home/user01/.hermes"
StandardOutput=journal
StandardError=journal
EOF

cat > ~/.config/systemd/user/hermes-skill-distill.timer <<'EOF'
[Unit]
Description=Daily Hermes skill distillation at 04:00

[Timer]
OnCalendar=*-*-* 04:00:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
EOF
```

### 4. Create Hourly Health Patrol Timer
```bash
cat > ~/.config/systemd/user/hermes-health-patrol.service <<'EOF'
[Unit]
Description=Hermes Hourly Health Patrol
After=network-online.target

[Service]
Type=oneshot
ExecStart=/home/user01/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main health patrol --quiet
WorkingDirectory=/home/user01/.hermes
Environment="PATH=/home/user01/.hermes/hermes-agent/venv/bin:/usr/bin:/bin"
Environment="HERMES_HOME=/home/user01/.hermes"
StandardOutput=journal
StandardError=journal
EOF

cat > ~/.config/systemd/user/hermes-health-patrol.timer <<'EOF'
[Unit]
Description=Hourly Hermes health patrol

[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=5m

[Install]
WantedBy=timers.target
EOF
```

### 5. Enable and Start All Timers
```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-daily-compress.timer
systemctl --user enable --now hermes-skill-distill.timer
systemctl --user enable --now hermes-health-patrol.timer
```

**Completion criterion:** `systemctl --user list-timers 'hermes*' --no-pager` shows all three timers with next elapsed times.

### 6. Verify Timer Execution
```bash
# Check last run
systemctl --user status hermes-daily-compress.service
journalctl --user -u hermes-daily-compress.service -n 20

# Manual trigger test
systemctl --user start hermes-daily-compress.service
journalctl --user -u hermes-daily-compress.service -f
```

## Pitfalls

- **Timer vs cron**: Systemd timers replace user crontab; don't run both for same task.
- **Persistent=true**: Ensures missed runs execute on next boot (important for laptops).
- **RandomizedDelaySec**: Prevents thundering herd if many timers at same time.
- **Venv path**: Must use absolute path to hermes venv python; `$PATH` not reliable in systemd.
- **WorkingDirectory**: Must be `~/.hermes` for config/context access.
- **Gateway conflict**: Compression/distillation need gateway stopped for Scope Recall writer lease.

## Verification

```bash
# 1. All timers listed and enabled
systemctl --user list-timers 'hermes*' --no-pager | grep -E "compress|distill|health"

# 2. Next elapsed times reasonable (within 24h)
systemctl --user list-timers 'hermes*' --no-pager

# 3. Service runs without error (manual test)
systemctl --user start hermes-daily-compress.service
systemctl --user status hermes-daily-compress.service
# Should show: Active: inactive (dead) after success
```

---

*Skill distilled from sessions 20260908_042140_65b6a3aa, cron_ead55c70d699_20260831_180001 (2+ occurrences: missing timers in health check, cron jobs defined but not installed as systemd). Pattern threshold met via recurring setup gap.*