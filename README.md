# Generate Changelog

A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `changelog.sh` and `SKILL.md` to your project root
2. Run: `bash changelog.sh`
3. Your `CHANGELOG.md` is ready

## Quick Start

```bash
# Generate changelog and write to CHANGELOG.md
bash changelog.sh

# Print to stdout (no file written)
bash changelog.sh --stdout

# Changes since a specific tag
bash changelog.sh --tag v1.0
```

## How It Works

- Finds the last git tag automatically
- Parses conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- Categorizes into **Added** / **Fixed** / **Changed** / **Removed**
- Outputs a Keep a Changelog–formatted file

## Requirements

- `git` (any recent version)
- `bash` 4.0+