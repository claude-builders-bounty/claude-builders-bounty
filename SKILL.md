# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Usage

```bash
python3 changelog.py              # Generate from current directory
python3 changelog.py /path/to/repo  # Generate from specific repo
```

## Command

`/generate-changelog` — generates CHANGELOG.md using `python3 changelog.py`

## How it works

1. Finds the most recent git tag
2. Fetches all commits since that tag
3. Auto-categorizes into: Added / Fixed / Changed / Removed
4. Outputs a formatted CHANGELOG.md

## Requirements

- Python 3.6+
- git
