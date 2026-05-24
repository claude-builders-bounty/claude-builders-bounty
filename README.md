# CHANGELOG Generator

A zero-dependency bash script that generates a structured `CHANGELOG.md` from a project's git history.

## Setup (3 steps)

1. **Copy** `changelog.sh` into your repository root
2. **Make executable**: `chmod +x changelog.sh`
3. **Run**: `bash changelog.sh`

## Usage

```bash
# Generate CHANGELOG.md (default output)
bash changelog.sh

# Specify custom output file
bash changelog.sh MY_CHANGELOG.md
```

## Features

- **Tag-aware**: Automatically detects the latest git tag and collects commits since that release
- **Auto-categorization**: Sorts commits into Added, Fixed, Changed, Removed
- **Conventional Commits**: Recognizes `feat:`, `fix:`, `refactor:`, `chore:`, `remove:`, `docs:`, etc.
- **Keyword fallback**: For non-conventional commits, categorizes by keywords (add, fix, update, delete, etc.)
- **Zero dependencies**: Pure bash — works anywhere with `git` installed

## How It Works

1. Finds the latest git tag (`git describe --tags --abbrev=0`)
2. Collects all non-merge commits since that tag
3. Categorizes each commit by conventional prefix or keyword match
4. Outputs a formatted Markdown changelog with sections per category

## Claude Code Integration

See [SKILL.md](SKILL.md) for use as a Claude Code `/generate-changelog` command.

## Sample Output

Generated from a test repository with conventional commits since `v1.0.0`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Since v1.0.0] — 2026-05-24

### Added

- feat(auth): add OAuth2 support (`5f179bf`) [2026-05-24]
- feat: add search functionality (`99acff6`) [2026-05-24]

### Fixed

- fix(api): handle rate limiting gracefully (`d53c2d7`) [2026-05-24]
- fix(ui): button alignment on mobile (`b31f8fa`) [2026-05-24]

### Changed

- chore: update dependencies (`ffc5b54`) [2026-05-24]
- refactor: simplify database queries (`2711a7b`) [2026-05-24]

### Removed

- remove: drop support for Node 14 (`1199437`) [2026-05-24]
```

## Requirements

- `git` installed and in `$PATH`
- Must be run inside a git repository
- Bash 4.0+ (uses associative arrays)

## License

MIT
