# Generate a Structured CHANGELOG from Git History

Generate a well-formatted `CHANGELOG.md` from git history. Commits are automatically categorized into *Added*, *Fixed*, *Changed*, *Removed*, *Security*, *Deprecated*, and *Other* sections using conventional commit prefixes (feat:, fix:, refactor:, etc.) with keyword-based fallback.

## Usage

### Command

```bash
# Bash (no dependencies)
bash generate-changelog.sh

# Python (more robust)
python generate_changelog.py
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--repo` / `[PATH]` | `.` | Path to git repository |
| `--output` / `[FILE]` | `CHANGELOG.md` | Output file path |
| `--tag-pattern` / `[PATTERN]` | `v*` | Git tag pattern |

### Aliases

`/generate-changelog` — Run from any repo root to generate or update `CHANGELOG.md`.

## How It Works

1. **Detect version** — Finds the last git tag matching `v*` pattern, sorted by semver
2. **Fetch commits** — Gets all commits since the last tag (or falls back to last 50)
3. **Categorize** — Parses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `remove:`, `docs:`, `test:`, `security:`, `deprecate:`)
4. **Generate** — Outputs a `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format with commit links

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2025-01-15

### Added
- New user authentication flow ([abc1234](https://github.com/owner/repo/commit/abc1234))

### Fixed
- Resolved memory leak in cache layer ([def5678](https://github.com/owner/repo/commit/def5678))

### Changed
- Upgraded dependencies to latest versions ([ghi9012](https://github.com/owner/repo/commit/ghi9012))

[v1.2.0]: https://github.com/owner/repo/compare/v1.1.0...v1.2.0
```

## Requirements

- **Bash version:** `git` only (no other dependencies)
- **Python version:** `git` + Python 3.8+ (stdlib only, no pip packages needed)
