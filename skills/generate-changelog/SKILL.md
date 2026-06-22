# Fix for Issue #1: [BOUNTY $50] SKILL: Generate a structured CHANGELOG from git history

:::filepath skills/generate-changelog/SKILL.md
---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
command: /generate-changelog
tags: [git, changelog, documentation, automation]
---

# Generate Changelog Skill

This skill generates a structured `CHANGELOG.md` from your project's git history.

## Usage

Run `/generate-changelog` to generate a changelog from commits since the last git tag.

### Options
- `/generate-changelog` - Generate changelog since last tag
- `/generate-changelog --all` - Generate changelog for all commits
- `/generate-changelog --from <tag>` - Generate changelog from specific tag
- `/generate-changelog --output <file>` - Custom output file (default: CHANGELOG.md)

## How It Works

1. **Fetches commits** since the last git tag (or all commits if no tags exist)
2. **Auto-categorizes** commits into sections:
   - **Added**: New features (keywords: `add`, `feat`, `new`, `create`, `implement`)
   - **Fixed**: Bug fixes (keywords: `fix`, `bug`, `patch`, `resolve`, `close`)
   - **Changed**: Updates/modifications (keywords: `update`, `change`, `modify`, `refactor`, `improve`)
   - **Removed**: Deletions (keywords: `remove`, `delete`, `deprecate`, `drop`)
3. **Outputs** a properly formatted `CHANGELOG.md`

## Implementation

When the user runs `/generate-changelog`, execute the following steps:

### Step 1: Determine the commit range