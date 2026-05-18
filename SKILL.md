---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Categorizes commits into Added / Fixed / Changed / Removed / Security sections. Works as a Claude Code skill (`/generate-changelog`) or standalone bash script.
version: "1.0"
author: Hermes Agent
tags: [git, changelog, automation, devops]
aliases: [/generate-changelog, /changelog]
requires: ["git", "python3"]
---

# Generate Changelog — SKILL.md

## Trigger
User says "generate changelog", "make a changelog", or "/generate-changelog"

## Usage

**As Claude Code skill:**
```
/generate-changelog [--since-tag <tag>] [--repo <path>] [--output <file>]
```

**As standalone script:**
```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since-tag`, `-t` | Start from this git tag | Last tag |
| `--repo`, `-r` | Repository path | Current dir |
| `--output`, `-o` | Output file | `CHANGELOG.md` |
| `--limit`, `-n` | Max commits to process | 500 |

## How It Works

1. **Fetch commits** from last git tag to HEAD (or all commits if no tag)
2. **Categorize** each commit using conventional commit prefixes:
   - `feat*` → **Added**
   - `fix*` → **Fixed**
   - `docs*`, `style*`, `refactor*`, `perf*`, `test*`, `build*`, `ci*`, `chore*` → **Changed**
   - `remove*` → **Removed**
   - `security*` → **Security**
3. **Fallback** keyword matching for non-conventional commits
4. **Output** a Keep a Changelog-formatted `CHANGELOG.md`

## Example

```bash
# Generate from last release tag
bash changelog.sh --repo ./my-project

# Generate from specific version
bash changelog.sh --since-tag v2.0.0 --repo . --output HISTORY.md
```

## Output Format

```markdown
# Changelog

## [2026-05-18]
### Added
- New user authentication flow (a1b2c3d)

### Fixed
- Resolve memory leak in connection pool (e5f6g7h)

### Changed
- Upgrade dependencies to latest versions (i9j0k1l)
```
