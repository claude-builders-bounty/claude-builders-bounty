# CHANGELOG Generator

A single-file Python script that generates a structured `CHANGELOG.md` from git history.

## Usage (3 steps)

```bash
# 1. Copy changelog.py into your repo
cp changelog.py /path/to/your/repo/

# 2. Run it (auto-detects last tag, or pass a tag/commit)
cd /path/to/your/repo
python changelog.py                    # since last tag
python changelog.py v1.0.0             # since specific tag
python changelog.py HEAD~20            # last 20 commits

# 3. It writes CHANGELOG.md — commit it
```

## Categories

| Category | Matches |
|----------|---------|
| **Added** | `feat:`, `add`, `new`, `implement`, `introduce` |
| **Changed** | `refactor:`, `update`, `improve`, `BREAKING CHANGE` |
| **Fixed** | `fix:`, `bugfix`, `hotfix`, `resolve` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate` |

## Sample output

```markdown
# Changelog

Generated on 2025-11-05

## Added

- Add user authentication flow (a1b2c3d)
- Introduce dark mode toggle (e4f5g6h)

## Fixed

- Fix crash on empty config file (i7j8k9l)
```
