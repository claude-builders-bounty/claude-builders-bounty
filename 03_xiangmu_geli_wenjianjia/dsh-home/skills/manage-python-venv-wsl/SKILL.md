---
name: manage-python-venv-wsl
description: "Create, activate, and use Python venvs in WSL avoiding PEP 668."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [python, venv, wsl, pep668, isolation]
    related_skills: [install-chromadb-wsl, verify-hermes-setup]
---

# Manage Python Venv in WSL

Create and use Python virtual environments in WSL to bypass PEP 668 externally-managed-environment restrictions.

## When to Use

- `pip install` fails with "externally-managed-environment" error
- Need isolated Python environment for Hermes skills or projects
- Want reproducible dependency sets per project/skill

## Prerequisites

- WSL2 with `python3-venv` package installed (`sudo apt install python3.12-venv`)
- Python 3.10+ available

## How to Run

```bash
# Create venv
python3 -m venv /path/to/venv

# Use venv python/pip directly (no activation needed)
/path/to/venv/bin/python -c "import pkg; print(pkg.__version__)"
/path/to/venv/bin/pip install package_name
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python3 -m venv /path/to/venv` | Create new venv |
| `/path/to/venv/bin/python` | Venv Python interpreter |
| `/path/to/venv/bin/pip` | Venv pip |
| `rm -rf /path/to/venv` | Delete venv |

## Procedure

### 1. Ensure `python3-venv` Is Installed

```bash
sudo apt update && sudo apt install -y python3.12-venv
# Or match your Python version: python3.11-venv, python3.10-venv
```

**Success criterion:** `python3 -m venv --help` shows usage (exit 0).

### 2. Create Virtual Environment

```bash
python3 -m venv /path/to/venv
```

**Success criterion:** Directory created with `bin/python`, `bin/pip`, `pyvenv.cfg`.

### 3. Use Venv Without Activation (Recommended for Scripts/Cron)

```bash
# Direct interpreter invocation — works in cron, scripts, terminal tool
/path/to/venv/bin/python -m pip install package_name
/path/to/venv/bin/python your_script.py
```

**Why not `source activate`:** Activation only affects current shell; cron/subprocesses don't inherit it. Direct path is reliable everywhere.

### 4. Verify Venv Works

```bash
/path/to/venv/bin/python -c "import sys; print(sys.prefix)"
```

**Success criterion:** Prints the venv path (not `/usr`).

## Pitfalls

- **Missing `python3-venv`**: `venv` module exists but `ensurepip` fails silently. Install the distro package.
- **Activation in cron/terminal tool**: Doesn't persist. Always use full path: `/path/to/venv/bin/python`.
- **Multiple Python versions**: `python3 -m venv` uses whichever `python3` points to. Be explicit: `/usr/bin/python3.12 -m venv ...`
- **WSL path vs Windows path**: Create venv on ext4 (`/home/user/...`), not `/mnt/c/...` (slow, permission issues).
- **uv preferred** — Faster, more reliable than pip/venv. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then `uv venv /path/to/venv` (creates venv + installs pip) and `uv pip install package`. uv handles Python version detection and isolation automatically.
- **Windows path mapping** — `D:/Ai/...` maps to `/mnt/d/Ai/...` in WSL. Use `/mnt/d/...` paths in WSL code; ChromaDB persist_dir must be on ext4 (`/home/user/...`) not `/mnt/...` for performance.

## Verification

1. `python3 -m venv /tmp/test_venv && /tmp/test_venv/bin/python -c "import sys; assert 'test_venv' in sys.prefix"` → exits 0
2. `/tmp/test_venv/bin/pip list` → shows only pip/setuptools
3. `rm -rf /tmp/test_venv` → cleanup

---

*Skill generated from session pattern analysis (manage-python-venv-wsl appeared in 3+ sessions).*