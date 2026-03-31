# Generate CHANGELOG Skill

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/geldbert/claude-builders-bounty.git

# 2. Install
cd claude-builders-bounty/skills/generate-changelog
./install.sh

# 3. Run
cd your-project
/generate-changelog
```

## What it does

1. Fetches commits since the last git tag
2. Auto-categorizes into: `Added`, `Fixed`, `Changed`, `Removed`
3. Outputs a properly formatted `CHANGELOG.md`

## Categorization Rules

| Commit Prefix | Category |
|---------------|----------|
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `change:`, `update:`, `refactor:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- Add new feature (#123)

### Fixed
- Resolve bug in module X (#124)

## [v1.0.0] - 2024-01-15

## [v0.9.0] - 2024-01-10
```

## Requirements

- Git 2.0+
- Bash 4.0+ (or compatible shell)

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition |
| `changelog.sh` | Core script |
| `install.sh` | Installation script |
| `README.md` | This file |

## Sample Output

Generated from OpenClaw repository:

```markdown
# Changelog

## [Unreleased]

### Fixed
- preserve Teams Entra JWT fallback on legacy validator errors

### Other
- Docs: add boundary AGENTS guides (#56647)
- feat(xai): add plugin-owned x_search onboarding
...
```

## Installation Details

The install script:
1. Creates `~/.claude/skills/generate-changelog/` directory
2. Copies `SKILL.md` and `changelog.sh`
3. Makes `changelog.sh` executable

After installation, use `/generate-changelog` in any Claude Code session within a git repository.