# Structured Git CHANGELOG Generator

Automatically generates a structured `CHANGELOG.md` from git commit history.

## 3-Step Setup
1. Place `changelog.py` and `changelog.sh` in your project root.
2. Run `bash changelog.sh` (or `python changelog.py`).
3. View your freshly generated `CHANGELOG.md`.

## Features
- **Auto-Categorization:** Groups commits into `Added`, `Fixed`, `Changed`, `Removed`.
- **Git Tag Aware:** Automatically parses commits since the last release tag.
- **Zero Dependencies:** Pure Python 3 standard library.
