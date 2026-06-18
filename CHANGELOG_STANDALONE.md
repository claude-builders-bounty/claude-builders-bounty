# Changelog Generator (`changelog.sh`)

A zero-dependency bash script that generates a structured `CHANGELOG.md` from git history.

## Features

- ✅ **Zero dependencies** — Pure bash + git
- ✅ **Conventional commits** — Parses `feat:`, `fix:`, `chore:`, `refactor:`, etc.
- ✅ **Auto-categorization** — Added / Fixed / Changed / Removed / Other
- ✅ **Tag-aware** — Uses last git tag as version
- ✅ **CLI flags** — `--stdout` for piping, `--tag=<name>` for custom range
- ✅ **Claude Code compatible** — Use as `/generate-changelog` skill

## Usage

```bash
# Generate CHANGELOG.md
./changelog.sh

# Output to stdout
./changelog.sh --stdout

# Generate since specific tag
./changelog.sh --tag=v1.0.0
```

## Installation

```bash
curl -sLO https://raw.githubusercontent.com/your-repo/main/changelog.sh
chmod +x changelog.sh
```

## Sample Output

```
# Changelog

## [0.0.0] — 2026-06-18

### 🚀 Added
- feat: add user authentication (af2860c)
- feat: add rate limiter (122ac4c)

### 🐛 Fixed
- fix: resolve memory leak (1a2b3c4)
```

## License

MIT
