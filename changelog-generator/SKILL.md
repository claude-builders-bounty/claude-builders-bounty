---
name: changelog-generator
description: >
  Generate a structured CHANGELOG.md from git history.
  Parses Conventional Commits and auto-categorizes into Added/Fixed/Changed/Removed.
  Works as both an agent skill and a standalone Python script.
---

# CHANGELOG Generator

Automatically generates a `CHANGELOG.md` from your project's git history.

## Usage

### As a skill command

Say "generate changelog" or "update changelog" — the agent runs the script for you.

### As a standalone script

```bash
# Generate from the last tag
python changelog.py

# From a specific tag
python changelog.py --since v1.0.0

# Custom output file
python changelog.py --output RELEASE.md
```

## What it does

1. Detects the last git tag (finds semver tags like `v1.0.0` automatically)
2. Fetches all commits since that tag
3. Parses Conventional Commit messages (`feat:`, `fix:`, `docs:`, etc.)
4. Auto-categorizes into:
   - **✨ Added** — new features (`feat:`, `feature:`, `add:`, `docs:`)
   - **🔄 Changed** — improvements, refactors, chores (`refactor:`, `perf:`, `style:`, `chore:`)
   - **🐛 Fixed** — bug fixes (`fix:`, `bugfix:`, `hotfix:`, `revert:`)
   - **🗑️ Removed** — deprecations (`remove:`, `delete:`, `deprecate:`)
5. Groups by scope when multiple scopes exist
6. Outputs `CHANGELOG.md`

## Requirements

- Python 3.8+
- git

No external dependencies — uses Python stdlib only.

## Sample output

```markdown
## [Unreleased]

### ✨ Added
  - **auth:** add OAuth2 login flow (a1b2c3d4)
  - **docs:** add API reference (e5f6g7h8)

### 🐛 Fixed
  - **core:** fix null pointer in session handler (i9j0k1l2)
  - fix typo in README (m3n4o5p6)

### 🔄 Changed
  - **build:** upgrade to Python 3.12 (q7r8s9t0)
  - **ci:** optimize test workflow (u1v2w3x4)
```
