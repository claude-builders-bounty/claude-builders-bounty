---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Fetches commits since the last git tag and auto-categorizes them into Added/Fixed/Changed/Removed sections following Keep a Changelog format.
---

# Generate CHANGELOG

Automatically generate a structured CHANGELOG.md from your project's git history.

## Quick Start

Run the skill:

```bash
/generate-changelog
```

Or use the bundled script directly:

```bash
bash scripts/generate-changelog.sh
```

## What It Does

1. Finds the most recent git tag in your repository
2. Fetches all commits since that tag
3. Categorizes commits by analyzing commit messages:
   - **Added** — new features, implementations
   - **Fixed** — bug fixes, patches
   - **Changed** — updates, refactors, improvements
   - **Removed** — deletions, deprecations
4. Generates a formatted CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format

## Categorization Logic

Commits are categorized by scanning for keywords in the commit message:

- **Added:** `add`, `new`, `feature`, `implement`, `introduce`
- **Fixed:** `fix`, `bug`, `patch`, `resolve`, `correct`
- **Changed:** `change`, `update`, `refactor`, `improve`, `modify`, `enhance`
- **Removed:** `remove`, `delete`, `deprecate`, `drop`

If no keyword matches, the commit goes into **Changed** by default.

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- New feature X
- Implement Y

### Fixed
- Fix bug Z
- Resolve issue #123

### Changed
- Update dependency A
- Refactor module B

### Removed
- Remove deprecated API
```

## Requirements

- Git repository with at least one tag
- Bash 4.0+ (or compatible shell)
- Standard Unix tools: `git`, `date`, `grep`, `sed`

## Usage Examples

### Generate changelog for current repo

```bash
/generate-changelog
```

### Preview without writing file

```bash
bash scripts/generate-changelog.sh --dry-run
```

### Specify output file

```bash
bash scripts/generate-changelog.sh --output HISTORY.md
```

## Troubleshooting

**No tags found:**
If your repo has no tags, the script will fetch all commits from the beginning. Consider creating a tag first:

```bash
git tag v0.1.0
```

**Empty changelog:**
If no commits are found, check that you're in a git repository and have commits:

```bash
git log --oneline
```

## Bundled Script

The skill includes `scripts/generate-changelog.sh` which can be used standalone or integrated into CI/CD pipelines.

See [scripts/README.md](scripts/README.md) for advanced usage.
