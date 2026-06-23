# CHANGELOG Generator

Auto-generate structured CHANGELOG.md from git history.

## Setup

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`

## Usage

```bash
# Generate from last tag to HEAD
bash changelog.sh

# Specify a custom since point
bash changelog.sh --since v1.0.0

# Custom output file
bash changelog.sh --output CHANGELOG.md
```

## How it works

The script scans conventional commits since the last tag:

| Prefix | Category |
|--------|----------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:/perf:/style:` | Changed |
| `remove:` | Removed |
