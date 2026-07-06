# Changelog Generator

Generate a structured `CHANGELOG.md` from your project's git history.

## Setup

1. Copy `changelog.sh` into your project root.
2. Make it executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

## Usage

```bash
bash changelog.sh [--since <tag>] [--to <commit>] [--output CHANGELOG.md]
```

- `--since`: Git ref to start from (default: latest tag)
- `--to`: Git ref to end at (default: HEAD)
- `--output`: Output file (default: CHANGELOG.md)

### Example

```bash
bash changelog.sh --since v1.0.0 --output CHANGELOG.md
```

## Categorization

Conventional commit prefixes are mapped:
- `feat:` → Added
- `fix:` → Fixed
- `refactor:`, `perf:` → Changed
- `removed:` → Removed
- Others → Other

## Requirements

- Git
- Bash (3.2+)
