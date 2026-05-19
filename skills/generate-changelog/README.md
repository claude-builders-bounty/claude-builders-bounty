# Generate Changelog Skill

Automatically generate a structured CHANGELOG.md from your project git history.

## Quick Start (3 steps)

1. Copy the skills/generate-changelog/ directory into your project
2. Run the script:
   bash skills/generate-changelog/changelog.sh
3. Review and commit the generated CHANGELOG.md

## Options

| Flag | Description | Default |
|------|-------------|---------|
| --from-tag TAG | Start from a specific tag | Auto-detects latest tag |
| --output FILE | Output file path | CHANGELOG.md |

## Commit Convention

The script auto-categorizes commits based on conventional prefixes:

| Prefix | Category |
|--------|----------|
| feat:, feature:, add: | Added |
| fix:, bugfix:, hotfix: | Fixed |
| change:, refactor:, update:, chore: | Changed |
| remove:, delete:, deprecate: | Removed |

Unrecognized commits are placed under Changed.

## Requirements

- Bash 4+
- Git
- No additional dependencies
