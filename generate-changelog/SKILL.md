# SKILL.md — Generate Changelog

**Command:** `/generate-changelog`

**What it does:**
Generates a structured `CHANGELOG.md` from a project's git history, auto-categorizing commits into Added / Fixed / Changed / Removed sections using conventional commit parsing.

**How to use:**
```bash
bash generate-changelog.sh [repo_path] [output_file]
# Or from any project:
bash /path/to/generate-changelog.sh .
```

**Requirements:**
- `git`
- `awk`, `sed`, `grep` (standard Unix tools on Linux/macOS, WSL on Windows)

**Output format:**
```markdown
# Changelog

## [Unreleased]

### Added
- feat: description

### Fixed
- fix: description

### Changed
- chore: description

### Removed
- refactor!: breaking change
```

**How it works:**
1. Finds the last git tag
2. Gets all commits since that tag (or last 50 commits if no tag)
3. Parses conventional commit format: `type(scope): message`
4. Categorizes by type into the four sections
5. Outputs a properly formatted CHANGELOG.md
