# Generate CHANGELOG Skill

> Automatically generate a structured CHANGELOG.md from git history

A Claude Code skill that fetches commits since the last git tag and categorizes them into Added/Fixed/Changed/Removed sections following [Keep a Changelog](https://keepachangelog.com/) format.

---

## Quick Setup

**1. Copy the skill to your Claude Code skills directory:**

```bash
cp -r skills/generate-changelog ~/.claude/skills/
```

**2. Use it in Claude Code:**

```
/generate-changelog
```

**3. Or run the script directly:**

```bash
bash skills/generate-changelog/scripts/generate-changelog.sh
```

That's it! ✅

---

## What It Does

- Finds the most recent git tag (or uses all commits if no tags exist)
- Fetches commits since that tag
- Auto-categorizes by scanning commit messages for keywords:
  - **Added:** `add`, `new`, `feature`, `implement`
  - **Fixed:** `fix`, `bug`, `patch`, `resolve`
  - **Changed:** `change`, `update`, `refactor`, `improve`
  - **Removed:** `remove`, `delete`, `deprecate`
- Generates a formatted `CHANGELOG.md`

---

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-05-15

_Generated from git history since v1.2.0._

### Added
- Add user authentication (a1b2c3d)
- Implement dark mode (e4f5g6h)

### Fixed
- Fix memory leak in parser (i7j8k9l)
- Resolve issue #42 (m0n1o2p)

### Changed
- Update dependencies (q3r4s5t)
- Refactor API client (u6v7w8x)

### Removed
- Remove deprecated endpoints (y9z0a1b)
```

---

## Options

```bash
# Preview without writing file
bash scripts/generate-changelog.sh --dry-run

# Specify output file
bash scripts/generate-changelog.sh --output HISTORY.md

# Show help
bash scripts/generate-changelog.sh --help
```

---

## Requirements

- Git repository with commits
- Bash 4.0+ (or compatible shell)
- Standard Unix tools: `git`, `date`, `grep`, `sed`

---

## Sample Output

See [samples/CHANGELOG-sample.md](samples/CHANGELOG-sample.md) for a real example generated from this repository.

---

## License

MIT
