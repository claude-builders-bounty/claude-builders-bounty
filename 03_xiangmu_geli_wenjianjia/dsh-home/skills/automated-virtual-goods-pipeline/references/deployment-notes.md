# Deployment Notes: Docker / Systemd / WSL2 Gotchas

## Docker Deployment

### Multi-Stage Build Targets

```dockerfile
# Base: Common dependencies, Playwright Chromium
FROM python:3.12-slim AS base

# Delivery: Long-running service (Phase 4)
FROM base AS delivery
ENTRYPOINT ["python", "main.py", "deliver", "--mode", "standalone"]

# Scheduler: Cron jobs (Phase 1-3)
FROM base AS scheduler
RUN pip install apscheduler
ENTRYPOINT ["python", "scripts/scheduler.py"]

# Dev: Debugging with vim, ipython, pytest
FROM base AS dev
RUN apt-get update && apt-get install -y vim && pip install pytest ipython
ENTRYPOINT ["/bin/bash"]
```

### Build Commands

```bash
# Build all targets
docker compose build

# Build specific target
docker compose build xianyu-delivery
docker compose build xianyu-scheduler

# No-cache rebuild
docker compose build --no-cache
```

### Runtime Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| `playwright: command not found` | Chromium not installed in image | `RUN python -m playwright install chromium --with-deps` in Dockerfile |
| `ModuleNotFoundError: pyxianyu` | Requirements not installed in target stage | Ensure `COPY requirements.txt` + `RUN pip install` in base stage |
| `Permission denied: /app/data` | Volume mounted as root | `RUN chown -R appuser:appuser /app` in Dockerfile |
| `WebSocket connection refused` | Container network isolation | Use `network_mode: host` or proper docker network |
| `Cookie not persisted` | Volume not mounted | Mount `./data:/app/data` in docker-compose |
| `Playwright: browser not found` | Chromium path mismatch | Set `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright` |

### docker-compose.yml Profiles

```yaml
services:
  xianyu-delivery:
    profiles: ["delivery"]  # Default profile
  
  xianyu-scheduler:
    profiles: ["scheduler"]  # Optional
  
  xianyusmart:
    profiles: ["xianyusmart"]  # Full stack
  
  mysql:
    profiles: ["xianyusmart"]
  
  redis:
    profiles: ["redis"]
```

**Usage:**
```bash
# Default (delivery only)
docker compose up -d

# With scheduler
docker compose --profile scheduler up -d

# Full XianYuSmart stack
docker compose --profile xianyusmart up -d
```

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 60s
  timeout: 10s
  retries: 3
  start_period: 30s
```

For XianYuSmart:
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "--spider", "http://localhost:12400/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Systemd (WSL2) Deployment

### Service Unit File

```ini
# ~/.config/systemd/user/xianyu-pipeline.service
[Unit]
Description=Xianyu Virtual Goods Pipeline
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/user01/.hermes/python/xianyu_pipeline
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/home/user01/.hermes/python/xianyu_pipeline/config/.env
ExecStart=/home/user01/.hermes/python/xianyu_pipeline/.venv/bin/python main.py deliver --mode standalone
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xianyu-pipeline

# Resource limits
MemoryLimit=2G
CPUQuota=200%

[Install]
WantedBy=default.target
```

### Timer for Scheduler (Phase 1-3)

```ini
# ~/.config/systemd/user/xianyu-pipeline-scheduler.timer
[Unit]
Description=Daily Xianyu Pipeline Scheduler

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=15min

[Install]
WantedBy=timers.target
```

```ini
# ~/.config/systemd/user/xianyu-pipeline-scheduler.service
[Unit]
Description=Xianyu Pipeline Scheduler Run
Requires=xianyu-pipeline-scheduler.service

[Service]
Type=oneshot
WorkingDirectory=/home/user01/.hermes/python/xianyu_pipeline
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/home/user01/.hermes/python/xianyu_pipeline/config/.env
ExecStart=/home/user01/.hermes/python/xianyu_pipeline/.venv/bin/python scripts/scheduler.py
StandardOutput=journal
StandardError=journal
```

### Enable Commands

```bash
# Enable user lingering (allows services to run without login)
loginctl enable-linger user01

# Reload daemon
systemctl --user daemon-reload

# Enable and start delivery service
systemctl --user enable --now xianyu-pipeline.service

# Enable and start scheduler timer
systemctl --user enable --now xianyu-pipeline-scheduler.timer

# Check status
systemctl --user status xianyu-pipeline.service
systemctl --user status xianyu-pipeline-scheduler.timer

# View logs
journalctl --user -u xianyu-pipeline -f
journalctl --user -u xianyu-pipeline-scheduler -f
```

### WSL2 Specific Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| `systemd` not running | WSL2 default | Enable in `/etc/wsl.conf`: `[boot] systemd=true` |
| `network-online.target` hangs | WSL2 network init | Add `After=network.target` instead of `network-online.target` |
| Volume mounts fail | 9p filesystem | Use `type=bind` in docker-compose, not `type=volume` |
| Time drift | No hardware clock | `sudo hwclock -s` or install `chrony` |
| `.venv` path too long | Windows MAX_PATH | Use short path: `/home/user01/xianyu_pipeline` |

## Environment Variables

### Required (All Deployments)

```bash
XIANYU_COOKIE="full_cookie_string"
```

### Recommended

```bash
OPENAI_API_KEY="sk-xxx"
GITHUB_TOKEN="ghp_xxx"
NETDISK_COOKIE="xxx"
FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
DINGTALK_WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=xxx"
```

### Docker-Specific

```bash
# In docker-compose.yml environment section
PYTHONUNBUFFERED=1
TZ=Asia/Shanghai
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

### Systemd-Specific

```bash
# In service file EnvironmentFile
# Or inline:
Environment=PYTHONUNBUFFERED=1
Environment=TZ=Asia/Shanghai
```

## Monitoring & Logs

### Docker Logs

```bash
# Follow delivery service
docker compose logs -f xianyu-delivery

# Follow scheduler
docker compose logs -f xianyu-scheduler

# All services
docker compose logs -f --tail=100
```

### Systemd Logs

```bash
# Follow delivery
journalctl --user -u xianyu-pipeline -f

# Follow scheduler
journalctl --user -u xianyu-pipeline-scheduler -f

# Since last boot
journalctl --user -u xianyu-pipeline -b
```

### Log Rotation

Docker: Built-in (json-file driver, max-size 10m, max-file 3)
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

Systemd: journald handles rotation (configure in `/etc/systemd/journald.conf`)

## Backup & Recovery

### Data to Backup

| Path | Content | Frequency |
|------|---------|-----------|
| `data/processed_orders.json` | Idempotency keys | Daily |
| `resources/cards/` | Card code inventory | Daily |
| `config/.env` | Configuration | On change |
| `output/` | Reports | Weekly |
| `logs/` | Debugging | Weekly |

### Backup Script (Cron)

```bash
#!/bin/bash
# /home/user01/backup_xianyu.sh
set -euo pipefail

BACKUP_DIR="/home/user01/backups/xianyu/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

cp /home/user01/.hermes/python/xianyu_pipeline/data/processed_orders.json "$BACKUP_DIR/"
cp -r /home/user01/.hermes/python/xianyu_pipeline/resources/cards "$BACKUP_DIR/"
cp /home/user01/.hermes/python/xianyu_pipeline/config/.env "$BACKUP_DIR/"
tar -czf "$BACKUP_DIR/output.tar.gz" -C /home/user01/.hermes/python/xianyu_pipeline output/
tar -czf "$BACKUP_DIR/logs.tar.gz" -C /home/user01/.hermes/python/xianyu_pipeline logs/

# Keep last 30 days
find /home/user01/backups/xianyu -type d -mtime +30 -exec rm -rf {} \;
```

Add to crontab: `0 3 * * * /home/user01/backup_xianyu.sh`

## Troubleshooting Quick Reference

| Symptom | Likely Cause | First Check |
|---------|--------------|-------------|
| No orders detected | Cookie expired / WS disconnected | `journalctl -u xianyu-pipeline | grep 401` |
| Publish fails | Sensitive words / API change | Check `logs/` for "敏感词" or "FAIL_BIZ" |
| Card code not delivered | Inventory empty / lock stuck | `cat resources/cards/*.txt \| wc -l` |
| Scheduler not running | Timer inactive / service failed | `systemctl --user status xianyu-pipeline-scheduler.timer` |
| High memory usage | Log accumulation / leak | `docker stats` / `journalctl --disk-usage` |
| Playwright timeout | Chromium crash / OOM | Increase container memory limit |