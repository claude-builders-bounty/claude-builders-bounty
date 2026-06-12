# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup

```bash
chmod +x changelog.py
```

## Usage

```bash
# Preview to stdout
python changelog.py

# Write to file
python changelog.py -o CHANGELOG.md
```

Auto-categorizes commits by conventional commit prefix (`feat:`, `fix:`, `chore:`, etc.) and falls back to keyword matching.
