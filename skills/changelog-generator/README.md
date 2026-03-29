# Changelog Generator Skill

A native Claude Code skill (and standalone bash script) that automatically parses your git history and generates a structured `CHANGELOG.md`.

## Features
- **Auto-detection**: Finds the last git tag and only parses commits since then.
- **Auto-categorization**: Uses conventional commit prefixes (`feat`, `fix`, `refactor`, `remove`) to sort commits into `Added`, `Fixed`, `Changed`, and `Removed` sections.
- **Claude Native**: Includes a `SKILL.md` file so Claude Code knows exactly how to trigger it.

## Installation

1. Copy the `SKILL.md` and `changelog.sh` into your project (e.g. into a `.claude/skills/` directory).
2. Make the script executable:
```bash
chmod +x changelog.sh
```

## Usage

**Option 1 (Claude Code)**:
Just ask Claude:
> `/generate-changelog` 
or 
> "Generate my changelog"

**Option 2 (Standalone CLI)**:
```bash
./changelog.sh
```

## Sample Output

```markdown
# Changelog

## [Unreleased] - 2026-03-29

### Added
- add n8n weekly github dev summary workflow (#5) (a66636b)
- add claude-review PR agent (#4) (8f94d66)

### Fixed
- patch typo in workflow variable (1a2b3c4)

### Changed
- refactor agent loop (5d6e7f8)
```
