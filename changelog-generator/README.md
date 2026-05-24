# CHANGELOG Generator

A bash script that generates a structured `CHANGELOG.md` from git history.

## Setup (2 steps)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`

## Usage

```bash
./changelog.sh
```

That's it. Run it in any git repo with tags.

## Example Output

```markdown
# Changelog

## [v1.2.0] - 2026-05-24

### Added
- feat: add dark mode toggle (#42)
- feat: support markdown export (#45)

### Fixed
- fix: handle empty state in dashboard (#43)
- fix: resolve memory leak in websocket handler (#47)

### Changed
- refactor: migrate to TypeScript strict mode (#44)

### Removed
- chore: drop legacy v1 API endpoints (#48)
```

## Options

| Flag | Description |
|------|-------------|
| `--output FILE` | Output file (default: CHANGELOG.md) |
| `--since TAG` | Start from a specific tag (default: latest tag) |
| `--dry-run` | Print to stdout instead of writing file |
| `--help` | Show help |
