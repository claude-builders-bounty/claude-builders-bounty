---
name: generate-changelog
description: Generate a Keep-a-Changelog compatible CHANGELOG.md categorized into Added, Fixed, Changed, and Removed by analyzing git commit history since the last tag.
input:
  type: object
  properties:
    repo_path:
      type: string
      description: The path to the git repository (defaults to current directory).
---

# Skill: Generate Structured Changelog

This skill automatically parses git history, identifies changes since the latest tag, categorizes conventional commits, and writes/prepends a standardized CHANGELOG.md.

## Execution

Invoke via Claude Code CLI:
/generate-changelog

Or via direct bash command:
bash changelog.sh

## Categorization Rules
- Added: Commits starting with feat, feature, add, or containing new functionality.
- Fixed: Commits starting with fix, bug, hotfix, or addressing issues.
- Changed: Commits with refactor, perf, style, docs, chore, update, or general modifications.
- Removed: Commits starting with remove, delete, or deprecate.
