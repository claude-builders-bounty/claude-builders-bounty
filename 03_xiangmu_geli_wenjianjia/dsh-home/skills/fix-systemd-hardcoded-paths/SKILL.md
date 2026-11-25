---
name: fix-systemd-hardcoded-paths
description: "Detect and fix hardcoded paths in systemd drop-ins."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [systemd, path-migration, hardcoded-paths, service-config, maintenance]
    related_skills: [manage-systemd-services-wsl, configure-feishu-gateway, wsl-hermes-system-health, proactive-health-patrol]
---

# Fix Systemd Hardcoded Paths

Detect and remediate hardcoded absolute paths in systemd user service drop-ins (`*.conf` files) and associated scripts that break when project directories move. Common after repository restructuring or WSL migrations.

## When to Use

- Service fails with "No such file or directory" for ExecStart/Environment paths
- Project directory moved (e.g., `~/.hermes/hermes-agent` → `~/projects/hermes-agent-src`)
- Health patrol reports path mismatches
- After git clone/reorg of hermes-agent source
- Cron jobs fail due to stale script paths

## Prerequisites

- WSL2 with systemd user services enabled
- `systemctl --user` access
- Read/write to `~/.config/systemd/user/<service>.service.d/`
- Python 3.11+ for path validation scripts

## How to Run

```bash
# Scan all user services for hardcoded paths
hermes chat -q "Scan systemd user services for hardcoded paths that may be stale"

# Fix specific service (interactive)
hermes chat -q "Fix hardcoded paths in hermes-gateway service drop-ins"

# Full audit + auto-fix
hermes chat -q "Run full systemd path audit: detect, validate, and fix all stale paths"
```

## Quick Reference

| Task | Command |
|------|---------|
| List all user service drop-ins | `find ~/.config/systemd/user -name "*.conf" -type f` |
| Check service environment | `systemctl --user show <service> --property=Environment` |
| Validate path exists | `test -f "/path/to/check" && echo EXISTS || echo MISSING` |
| Reload daemon after changes | `systemctl --user daemon-reload` |
| Restart service | `systemctl --user restart <service>` |
| View service status | `systemctl --user status <service> --no-pager` |

## Procedure

### 1. Discover All Service Drop-ins

```bash
# Find all drop-in directories and config files
find ~/.config/systemd/user -name "*.conf" -type f | while read conf; do
    echo "=== $conf ==="
    cat "$conf"
done
```

**Completion criterion**: Complete inventory of all `.conf` files with their content.

### 2. Extract and Validate Paths

```python
#!/usr/bin/env python3
# Path validation script
import os, re, subprocess, sys

PATH_PATTERNS = [
    r'(ExecStart|ExecReload|ExecStop|Environment=)\s*=?\s*["\']?(/[^"\'\s]+)',
    r'(WorkingDirectory|RuntimeDirectory|StateDirectory)\s*=\s*["\']?(/[^"\'\s]+)',
]

def extract_paths_from_conf(conf_path):
    paths = []
    with open(conf_path) as f:
        content = f.read()
    for pattern in PATH_PATTERNS:
        for match in re.finditer(pattern, content):
            path = match.group(2) if match.lastindex >= 2 else match.group(1)
            paths.append((conf_path, path.strip('"\'')))
    return paths

def validate_path(path):
    # Expand ~ and env vars
    path = os.path.expanduser(os.path.expandvars(path))
    return os.path.exists(path)

# Scan all drop-ins
all_paths = []
for root, dirs, files in os.walk(os.path.expanduser("~/.config/systemd/user")):
    for f in files:
        if f.endswith(".conf"):
            conf_path = os.path.join(root, f)
            all_paths.extend(extract_paths_from_conf(conf_path))

# Report
print(f"Found {len(all_paths)} path references:")
for conf, path in all_paths:
    expanded = os.path.expanduser(os.path.expandvars(path))
    exists = "✅" if os.path.exists(expanded) else "❌"
    print(f"  {exists} {conf}: {path} → {expanded}")
```

**Completion criterion**: All paths extracted; each marked EXIST/MISSING.

### 3. Identify Stale Path Patterns

| Pattern | Example (Stale) | Example (Fixed) | Detection |
|---------|-----------------|-----------------|-----------|
| Old hermes-agent venv | `/home/user01/.hermes/hermes-agent/venv/bin/hermes` | `/home/user01/projects/hermes-agent-src/venv/bin/hermes` | Check if parent dir exists |
| Old Python binary | `/home/user01/.hermes/hermes-agent/venv/bin/python3` | `/home/user01/projects/hermes-agent-src/venv/bin/python3` | Check symlink target |
| Windows literal D: path | `D:/Ai/Ollama/Memory/chroma` | `/home/user01/.hermes/chroma` | Check `/mnt/d` mount + existence |
| Old cua-driver path | `/mnt/c/Users/.../cua-driver/bin/cua-driver.exe` | `/mnt/c/Users/Administrator/AppData/Local/Programs/Cua/cua-driver/bin/cua-driver.exe` | Check actual install location |

**Completion criterion**: Stale paths categorized by pattern; fix strategy determined.

### 4. Apply Fixes

```bash
# For each stale path in drop-in files:
# 1. Backup original
cp ~/.config/systemd/user/hermes-gateway.service.d/feishu-secret.conf \
   ~/.config/systemd/user/hermes-gateway.service.d/feishu-secret.conf.bak.$(date +%s)

# 2. Update path (example: fix HERMES_CLI)
sed -i 's|/home/user01/.hermes/hermes-agent/venv/bin/hermes|/home/user01/projects/hermes-agent-src/venv/bin/hermes|g' \
    ~/.config/systemd/user/hermes-gateway.service.d/*.conf

# 3. Update Python binary
sed -i 's|/home/user01/.hermes/hermes-agent/venv/bin/python3|/home/user01/projects/hermes-agent-src/venv/bin/python3|g' \
    ~/.config/systemd/user/hermes-gateway.service.d/*.conf

# 4. Fix ChromaDB path in scripts (not drop-ins)
sed -i 's|/mnt/d/Ai/Ollama/Memory/chroma|/home/user01/.hermes/chroma|g' \
    /home/user01/.hermes/scripts/proactive_patrol.py \
    /home/user01/.hermes/scripts/health_check.py
```

**Completion criterion**: All stale paths replaced; backups created.

### 5. Reload and Verify

```bash
# Reload systemd
systemctl --user daemon-reload

# Restart affected services
for svc in hermes-gateway hermes-daily-compress hermes-skill-distill; do
    systemctl --user restart "$svc" 2>/dev/null || true
done

# Verify each service
for svc in hermes-gateway hermes-daily-compress hermes-skill-distill; do
    systemctl --user status "$svc" --no-pager | grep -q "active (running)" \
        && echo "✅ $svc: running" \
        || echo "❌ $svc: FAILED"
done

# Verify environment propagated
systemctl --user show hermes-gateway --property=Environment | grep -E "HERMES_CLI|PYTHON_BIN|HERMES_CUA_DRIVER_CMD"
```

**Completion criterion**: All services active (running); environment shows correct paths.

### 6. Validate Scripts Using Fixed Paths

```bash
# Test critical scripts
/home/user01/projects/hermes-agent-src/venv/bin/python3 -c "import hermes_cli; print('CLI imports OK')"
/home/user01/projects/hermes-agent-src/venv/bin/hermes --version
```

**Completion criterion**: Scripts execute without path errors.

## Pitfalls

| Issue | Solution |
|-------|----------|
| Multiple drop-ins for same service | Check all `.conf` files in the service's `.d/` directory |
| Environment vars in drop-ins not expanded by systemd | Use absolute paths; systemd doesn't expand `~` or `$HOME` in `Environment=` |
| Paths in Python scripts (not drop-ins) | Grep scripts directory separately: `grep -r "/home/user01/.hermes/hermes-agent" /home/user01/.hermes/scripts/` |
| Service has `ProtectSystem=strict` | Path must be in allowed directories or use `ReadWritePaths=` |
| Symlinks vs real paths | Validate with `readlink -f` to ensure target exists |
| Windows paths in WSL drop-ins | Use `/mnt/c/...` format; avoid `C:\...` literals |

## Verification

```bash
# 1. No stale paths remain
python3 << 'EOF'
import os, re, subprocess
stale_patterns = [
    r"/home/user01/\.hermes/hermes-agent/venv",
    r"D:/Ai/Ollama/Memory/chroma",
    r"D:\\Ai\\Ollama",
]
found = False
for root, dirs, files in os.walk(os.path.expanduser("~/.config/systemd/user")):
    for f in files:
        if f.endswith(".conf"):
            content = open(os.path.join(root, f)).read()
            for pat in stale_patterns:
                if re.search(pat, content):
                    print(f"STALE PATH in {root}/{f}: {pat}")
                    found = True
if not found:
    print("✅ No stale paths in systemd drop-ins")
EOF

# 2. All services healthy
systemctl --user list-units --state=failed --no-pager | grep -q hermes && echo "❌ Failed services exist" || echo "✅ No failed hermes services"

# 3. Key executables resolve
for cmd in hermes python3; do
    path=$(systemctl --user show hermes-gateway --property=Environment | grep -oP "(?<=$cmd=)[^\s]+" | head -1)
    test -x "$path" && echo "✅ $cmd: $path" || echo "❌ $cmd: NOT FOUND at $path"
done
```

---

*Distilled from 3+ incidents (Sep 26, 30, Oct 1, 2026): proactive_patrol.py hardcoded paths broke after hermes-agent moved from `~/.hermes/hermes-agent` to `~/projects/hermes-agent-src`; ChromaDB path `D:/Ai/Ollama/Memory/chroma` stale after migration to `~/.hermes/chroma`; cua-driver path outdated. Pattern: any repo restructure breaks systemd drop-ins and scripts referencing old absolute paths.*