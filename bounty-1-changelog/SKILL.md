---
name: generate-changelog
description: Generate a CHANGELOG from git history since the last tag
command: bash /path/to/changelog.sh
trigger: /generate-changelog
---

# /generate-changelog

Generate a formatted CHANGELOG from git commit history.

## What it does

1. Finds the latest git tag (or uses the first commit if no tags exist)
2. Collects all commits between that tag and HEAD
3. Categorizes each commit into **Added**, **Fixed**, **Changed**, or **Removed**
4. Outputs a formatted Markdown changelog

## Categorization strategy

| Priority | Method | Example |
|----------|--------|---------|
| 1st | Conventional commit prefix | `feat:`, `fix:`, `remove:` |
| 2nd | Keyword matching | "add feature", "fix bug", "remove handler" |
| 3rd | Default | Falls back to **Changed** |

## Installation

Add to your Claude Code settings (`.claude/settings.json`):

```json
{
  "skills": [
    {
      "name": "generate-changelog",
      "command": "bash bounty-1-changelog/changelog.sh",
      "description": "Generate CHANGELOG from git history"
    }
  ]
}
```

## Options

```
--from <ref>       Start ref (default: latest tag)
--to <ref>         End ref (default: HEAD)
--output <file>    Write to file instead of stdout
--version <ver>    Version label (default: Unreleased)
```
