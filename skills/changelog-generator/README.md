# Changelog Generator — Claude Code Skill

## What This Is

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history, categorizing commits into Added / Fixed / Changed / Removed sections.

## Installation

### Option 1: As a Claude Code Skill

```bash
mkdir -p ~/.claude/commands
curl -o ~/.claude/commands/generate-changelog.sh \
  https://raw.githubusercontent.com/YOUR_USER/changelog-generator/main/changelog.sh
chmod +x ~/.claude/commands/generate-changelog.sh
```

### Option 2: Standalone

```bash
git clone https://github.com/YOUR_USER/changelog-generator.git
cd changelog-generator
bash changelog.sh [v1.0.0] [CHANGELOG.md]
```

## Usage

```bash
# Generate since last git tag
bash changelog.sh

# Generate since a specific tag
bash changelog.sh v1.0.0

# Custom output file
bash changelog.sh v1.0.0 MY_CHANGELOG.md
```

## How It Works

1. Detects the last git tag (or uses `--all` for full history)
2. Parses commits using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` / `feat!:` → **Added**
   - `fix:` / `fix!:` → **Fixed**
   - `refactor:`, `perf:`, `test:`, `style:`, `ci:`, `docs:` → **Changed**
   - `BREAKING CHANGE`, `chore(removed):`, `remove:` → **Removed**
3. Auto-links commit hashes to GitHub
4. Outputs clean Markdown

## Example Output

```markdown
# Changelog

## [v1.2.0] (2026-04-10)

### Added
- New OAuth2 authentication flow ([`a3f9c21`](https://github.com/example/repo/commit/a3f9c21))
- Rate limiting middleware ([`b7d2e10`](https://github.com/example/repo/commit/b7d2e10))

### Fixed
- Fix memory leak in connection pool ([`c1a8f33`](https://github.com/example/repo/commit/c1a8f33))

### Changed
- Refactor database layer for 2x performance ([`d9e4a12`](https://github.com/example/repo/commit/d9e4a12))

### Removed
- ~~Legacy v1 API endpoints~~ (breaking change)

_Generated 2026-04-14 by changelog-generator_
```

## Setup (3 Steps or Fewer)

1. `git clone https://github.com/YOUR_USER/changelog-generator.git`
2. `cd changelog-generator && chmod +x changelog.sh`
3. `bash changelog.sh` — generates `CHANGELOG.md` in your project

## Tested On

- GitHub repos with conventional commits
- Monorepos (use `--since=tag` to scope)
- Works on macOS (BSD git) and Linux (GNU git)
