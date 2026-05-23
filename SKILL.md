# /generate-changelog — Auto-generate CHANGELOG.md from git history

A Claude Code skill that generates a structured CHANGELOG.md from git history using conventional commit parsing.

## Usage

In Claude Code, run:

```
/generate-changelog [--since TAG] [--output FILE]
```

Or directly from the command line:

```bash
python3 changelog.py --since $(git describe --tags --abbrev=0)
```

## What it does

- Fetches commits since the last git tag (or a specified tag)
- Auto-categorizes into: **Added**, **Fixed**, **Changed**, **Removed**
- Outputs a properly formatted CHANGELOG.md
- Supports Markdown, HTML, and JSON output formats
- Zero external dependencies (pure Python 3 stdlib)

## Requirements

- Python 3.8+
- Git repository with conventional commit messages

## Files

- `changelog.py` — The changelog generator script
- `README.md` — Setup instructions in 3 steps
