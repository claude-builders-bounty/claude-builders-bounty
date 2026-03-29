# SKILL.md — Generate Structured CHANGELOG from Git History

**Trigger:** `/generate-changelog` or `/changelog` or natural language like "generate a changelog"

**What it does:**
Automatically generates a structured `CHANGELOG.md` from a project's git history. Categorizes commits into Added / Fixed / Changed / Removed sections using conventional commit parsing.

---

## How to Use

```bash
# From any project directory
bash ~/.claude/skills/changelog/changelog.sh

# With options
bash ~/.claude/skills/changelog/changelog.sh . CHANGELOG.md
bash ~/.claude/skills/changelog/changelog.sh --version v1.0.0
bash ~/.claude/skills/changelog/changelog.sh --all   # all commits, no tag required
```

**Natural language triggers:**
- "Generate a changelog"
- "Update the changelog"
- "What changed since the last release?"
- "Show me the project history"

---

## Requirements

| Tool | Required | Notes |
|------|----------|-------|
| `git` | ✅ Yes | For reading commit history |
| `bash` | ✅ Yes | Linux/macOS/WSL |
| `python3` | Optional | For `changelog.py` (Windows-native alternative) |

---

## Output Format

Follows [Keep a Changelog 1.0.0](https://keepachangelog.com/en/1.0.0/):

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- feat: user authentication with JWT
- feat: dark mode support

### Fixed
- fix: resolve memory leak in cache layer

### Changed
- chore: upgrade dependencies to latest versions

### Removed
- refactor!: remove deprecated v1 API endpoints
```

---

## Categorization Rules

| Prefix | Category |
|--------|----------|
| `feat:`, `add:` | **Added** |
| `fix:`, `bug:` | **Fixed** |
| `chore:`, `ci:`, `build:`, `deps:` | **Changed** |
| `refactor!:`, `BREAKING CHANGE:` | **Removed** (breaking) |
| `docs:`, `test:`, `perf:` | **Changed** |
| Unrecognized | **Changed** |

---

## Auto-Versioning

- **Has tags:** Uses last tag as the version header (e.g., `## [v1.2.0] - 2026-03-29`)
- **No tags:** Uses `## [Unreleased]` header
- **Range mode:** `bash changelog.sh v1.0..v2.0` for any commit range

---

## Design Decisions

1. **Zero dependencies** — Pure bash + git. No Python, Node, or external tools required for basic use.
2. **Preserves existing CHANGELOG** — If `CHANGELOG.md` already exists with content, prepends new entries without overwriting.
3. **Fail gracefully** — If no conventional commits found, falls back to keyword detection.
4. **Merge-safe** — Skips `Merge pull request` and merge commits automatically.

---

## Files

| File | Purpose |
|------|---------|
| `changelog.sh` | Main bash script (Unix/Linux/macOS/WSL) |
| `changelog.py` | Cross-platform Python alternative (Windows-native) |
| `README.md` | Setup instructions and documentation |
| `sample-output/CHANGELOG.md` | Sample output from testing on a real repo |
