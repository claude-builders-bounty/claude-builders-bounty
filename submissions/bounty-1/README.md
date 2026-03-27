# CHANGELOG Generator

A bash script that generates a structured `CHANGELOG.md` from git commit history.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

## Usage

```bash
# Generate from last git tag to HEAD
bash changelog.sh

# Generate from a specific tag
bash changelog.sh v1.2.0

# Specify output file
bash changelog.sh v1.2.0 MY_CHANGELOG.md
```

## How It Works

Parses [Conventional Commits](https://www.conventionalcommits.org/) prefixes:

| Prefix | Section |
|--------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `chore:`, `docs:` | Changed |
| `remove:`, `delete:` | Removed |
| `breaking:` | Changed (⚠️) |

Non-conventional commits go into **Other**.

## Sample Output

```markdown
# Changelog

## [Unreleased] - 2026-03-27

### Added
- user authentication with JWT tokens
- dark mode toggle

### Fixed  
- crash when config file missing

### Changed
- extract validation to utils module
```
