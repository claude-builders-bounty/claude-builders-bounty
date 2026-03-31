# Generate CHANGELOG Skill

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

In Claude Code, use:
```
/generate-changelog
```

Or run directly:
```bash
bash ~/.claude/skills/generate-changelog/changelog.sh
```

## What it does

1. Fetches commits since the last git tag (or all commits if no tags)
2. Auto-categorizes changes into: `Added`, `Fixed`, `Changed`, `Removed`
3. Outputs a properly formatted `CHANGELOG.md`

## Categorization Rules

| Pattern | Category |
|---------|----------|
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `change:`, `update:`, `refactor:`, `improve:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |

Commits not matching any pattern go to `Other`.

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- feat: Add new feature (#123)

### Fixed
- fix: Resolve bug in module X (#124)

### Changed
- refactor: Improve performance (#125)

### Removed
- remove: Deprecate old API (#126)

## [1.0.0] - 2024-01-15
...
```

## Installation

```bash
# Clone and install
git clone https://github.com/geldbert/claude-builders-bounty.git
cd claude-builders-bounty/skills/generate-changelog
./install.sh
```

## Requirements

- Git 2.0+
- Bash 4.0+
- Claude Code (for `/generate-changelog` command)