# generate-changelog

> **[Bounty #1]** A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from git history.

---

## Setup (3 steps)

1. **Clone or download** this repository / copy `changelog.sh` and `SKILL.md` to your project root.

2. **Make it executable:**
   ```bash
   chmod +x changelog.sh
   ```

3. **Run it:**
   ```bash
   bash changelog.sh
   ```

That's it — your `CHANGELOG.md` is ready. ✅

---

## Usage

### Via bash directly

```bash
# Basic usage (auto-detects latest git tag)
bash changelog.sh

# From a specific tag
bash changelog.sh --since v1.2.3

# Custom output file
bash changelog.sh --output RELEASE_NOTES.md

# Help
bash changelog.sh --help
```

### Via Claude Code skill

Add `SKILL.md` to your `.claude/skills/generate-changelog/` directory, then use:

```
/generate-changelog
```

---

## How it categorizes commits

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:`, `implement:` | **Added** |
| `fix:`, `bug:`, `patch:`, `hotfix:` | **Fixed** |
| `refactor:`, `update:`, `chore:`, `ci:`, `docs:`, `perf:` | **Changed** |
| `remove:`, `delete:`, `deprecate:`, `drop:` | **Removed** |
| Everything else | **Other** |

---

## Sample output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

---

## [Unreleased] — 2026-07-02

### Added
- feat: add user authentication module (`a1b2c3d`) — Alice

### Fixed
- fix: resolve null pointer in payment flow (`d4e5f6g`) — Bob

### Changed
- refactor: extract database layer into service (`h7i8j9k`) — Charlie
```

---

## Requirements

- **bash** 4.0+ (uses `mapfile`, associative arrays)
- **git** (any modern version)

No external dependencies. Works on macOS (with bash 4 from Homebrew) and Linux.
