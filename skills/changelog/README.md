# CHANGELOG Generator

Generate structured `CHANGELOG.md` from git history in 1 command.

## Setup (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.py

# 2. Make sure you have Python 3.6+
python3 --version

# 3. Run it
python3 changelog.py --write
```

Or use the bash version:
```bash
bash changelog.sh --write
```

That's it. Your `CHANGELOG.md` is generated.

## Claude Code Skill

Add `SKILL.md` to your project, then type `/generate-changelog` in Claude Code.

## Requirements

- **Python version**: Python 3.6+ (no pip packages needed — pure stdlib)
- **Bash version**: bash 4+, git, and standard Unix tools (sed, cut)
- **Git**: Must be run inside a git repository

## Options

| Flag | Description |
|------|-------------|
| `--write` / `-w` | Write to `CHANGELOG.md` file |
| `--version X.Y.Z` / `-v` | Override version (default: last git tag) |
| `--repo-url URL` / `-u` | Override repo URL for commit links |
| `--sample` / `-s` | Generate demo output (no git repo needed) |
| `--help` / `-h` | Show full help |

## How It Works

- Detects the last git tag and collects all commits since then
- Parses [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.)
- Falls back to keyword matching for non-standard messages
- Groups commits into: Added, Fixed, Changed, Removed, Deprecated, Security, Performance, Documentation, Infrastructure
- Links commit SHAs to your repository

## Sample Output

```
# Changelog

## [1.0.0] - 2026-05-16

### Added
- AI-powered commit categorization (a1b2c3d4)

### Fixed
- Handle empty git repos gracefully (e5f6g7h8)

### Changed
- Simplify classification logic (m3n4o5p6)
```

## Demo

```
python3 changelog.py --sample
```
