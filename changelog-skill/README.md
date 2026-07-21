# CHANGELOG Generator

A Python script that generates structured `CHANGELOG.md` from git history using Conventional Commits.

## Features

- Parses conventional commit format: `type(scope)!: description`
- Auto-categorizes into: **Breaking Changes**, **Added**, **Fixed**, **Changed**, **Removed**
- Groups by version tag (since last tag by default)
- Outputs Keep a Changelog 1.1.0 format
- Zero dependencies (stdlib only)

## Install

```bash
# Just copy the file
cp changelog.py /your/project/changelog.py
chmod +x changelog.py
```

## Usage

```bash
# Generate since last tag
python changelog.py

# Since specific tag
python changelog.py --since v1.2.0

# Write to file
python changelog.py --output CHANGELOG.md

# Include uncommitted changes
python changelog.py --unreleased
```

## Example Output

```markdown
# Changelog

## [v1.3.0] - 2026-07-19

### Breaking Changes
- feat(auth)!: require MFA for admin routes (`a1b2c3d`)

### Added
- feat(billing): add Stripe webhook handler (`e4f5g6h`)
- feat(api): add user export endpoint (`i7j8k9l`)

### Fixed
- fix(db): handle null timestamps in migrations (`m0n1o2p`)

### Changed
- refactor(cache): simplify Redis connection pooling (`q3r4s5t`)

### Removed
- remove(legacy): drop deprecated /v1 endpoints (`u6v7w8x`)
```

## For Claude Code (SKILL.md)

```markdown
# SKILL.md — Changelog Generator

## Description
Generate a structured CHANGELOG.md from git history. Categorizes commits into Breaking Changes, Added, Fixed, Changed, Removed using Conventional Commits.

## Usage
Trigger with `/generate-changelog` or run `python changelog.py`.

## Instructions
1. Run `changelog.py` in project root
2. Script auto-detects last tag and parses commits since then
3. Outputs Keep a Changelog format to stdout or file
4. Supports `--since <tag>`, `--output <file>`, `--unreleased`
```

## Requirements

- Python 3.8+
- Git repository with conventional commits

## License

MIT