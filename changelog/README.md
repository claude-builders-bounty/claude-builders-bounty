# Changelog Generator

Generate structured CHANGELOG.md from git history.

## Usage

```bash
bash generate-changelog.sh [OPTIONS]
```

### Options
- `--since-tag TAG` — Generate from specific tag (default: last tag)
- `--output FILE` — Output file (default: CHANGELOG.md)

## Installation

```bash
cp generate-changelog.sh /your/project/
cd /your/project && bash generate-changelog.sh
```
