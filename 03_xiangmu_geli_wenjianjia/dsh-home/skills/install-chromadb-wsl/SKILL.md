---
name: install-chromadb-wsl
description: Install and verify ChromaDB in WSL with proper venv handling.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [chromadb, wsl, vector-db, installation]
    related_skills: [manage-python-venv-wsl, verify-hermes-setup]
---

# Install ChromaDB in WSL

Install ChromaDB in WSL environments, handling PEP 668 externally-managed-environment errors and virtual environment isolation.

## When to Use

- Need ChromaDB for vector memory/embeddings in WSL
- `pip install chromadb` fails with "externally-managed-environment"
- Want isolated venv for Hermes skills (recommended) or user-site fallback

## Prerequisites

- WSL2 with Python 3.10+
- Either: project venv at `/path/to/project/venv` OR user-site (`--break-system-packages`)
- Internet access for PyPI downloads

## How to Run

```bash
# Option A: Project venv (recommended for Hermes skills)
/path/to/project/venv/bin/pip install chromadb

# Option B: User-site (no venv)
pip install chromadb --break-system-packages
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python -c "import chromadb; print(chromadb.__version__)"` | Verify import |
| `pip show chromadb` | Show installed version/location |
| `python -c "import chromadb; client = chromadb.Client(); print('OK')"` | Functional test |

## Procedure

### 1. Choose Installation Target

**Project venv (preferred):**
```bash
# Ensure venv exists
python3 -m venv /path/to/project/venv
# Install
/path/to/project/venv/bin/pip install chromadb
```

**User-site (fallback):**
```bash
pip install chromadb --break-system-packages
```

### 2. Verify Installation

```bash
# Using the same python that will run your code
/path/to/python -c "import chromadb; print(chromadb.__version__)"
```

**Success criterion:** Prints version (e.g., `1.5.9`) with no `ModuleNotFoundError`.

### 3. Functional Smoke Test

```bash
/path/to/python -c "
import chromadb
client = chromadb.Client()
col = client.create_collection('test')
col.add(documents=['hello'], ids=['1'])
results = col.query(query_texts=['hello'], n_results=1)
print('ChromaDB functional:', len(results['documents'][0]) == 1)
"
```

**Success criterion:** Prints `ChromaDB functional: True`.

## Pitfalls

- **PEP 668**: System Python blocks `pip install`. Fix: use venv or `--break-system-packages`.
- **Wrong interpreter**: `python3` vs venv `python` — always use the exact interpreter your app uses.
- **Timeout on large deps**: ChromaDB pulls ~200 MB. Use `timeout=300` or `background=true` in terminal tool.
- **WSL filesystem perf**: ChromaDB on `/mnt/c/` is slow. Keep persist_dir on ext4 (e.g., `/home/user/.chroma`).
- **Python version mismatch** — System Python 3.11 vs `pip` pointing to 3.12. Fix: use `python3.11 -m pip` or create venv with explicit version: `python3.11 -m venv venv`.
- **uv preferred** — Faster, more reliable than pip. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then `uv venv` + `uv pip install chromadb`.
- **Windows path mapping** — `D:/Ai/Ollama/Memory/chroma` maps to `/mnt/d/Ai/Ollama/Memory/chroma` in WSL. Use `/mnt/d/...` in WSL code.

## Verification

Run all three checks; all must pass:

1. `import chromadb` — no error
2. `chromadb.__version__` — prints version
3. Create → add → query roundtrip — returns expected result

---

*Skill generated from session pattern analysis (install-chromadb-wsl appeared in 3+ sessions).*