---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history. Use when user wants to create a changelog, release notes, or track project changes from git commits. Covers semantic commit parsing, git tag-based versioning, and standard keepachangelog format output.
---

# Changelog Generator

Generates a `CHANGELOG.md` from git commit history using semantic commit conventions.

## Usage

```bash
bash changelog.sh
```

## How It Works

1. Detects the last git tag — if none exists, uses all commits
2. Parses each commit message using conventional commit prefixes:
   - `feat:` / `add:` → **Added**
   - `fix:` / `bug:` / `patch:` → **Fixed**
   - `remove:` / `delete:` / `deprecate:` → **Removed**
   - Everything else → **Changed**
3. Outputs `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/) format

## Requirements

- Git repository
- Bash 4.0+
- No external dependencies

## Example Output

```markdown
# Changelog

## my-project

All notable changes are documented here.

### Added
- feat: user authentication system
- add: dark mode toggle

### Fixed
- fix: resolve session timeout bug

### Changed
- change: migrate to PostgreSQL

### Removed
- remove: deprecated v1 API endpoints
```

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Run `chmod +x changelog.sh`
3. Run `./changelog.sh`

## Tips

- Tag releases before running to scope output to changes since last release:
  ```bash
  git tag v1.0.0
  ./changelog.sh
  ```
- Combine with CI: run `changelog.sh` on every merge to `main`
- Commit messages should follow [Conventional Commits](https://www.conventionalcommits.org/)
