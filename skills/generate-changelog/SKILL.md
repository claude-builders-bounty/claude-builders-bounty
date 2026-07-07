# Generate CHANGELOG

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history.

## Usage

```
# In any git repository:
./generate-changelog
# Or specify output file:
./generate-changelog CHANGELOG.md
```

## How it works

1. Detects all version tags in the repository
2. Categorizes commits by type (feat, fix, etc.)
3. Generates a Keep a Changelog-formatted file
4. Includes unreleased changes since the last tag

## Installation

Add this skill to your Claude Code hooks:

```bash
mkdir -p ~/.claude/skills/
cp generate-changelog ~/.claude/skills/
chmod +x ~/.claude/skills/generate-changelog
```
