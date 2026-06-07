---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from a project's git history
---

# Generate Changelog

Generates a structured `CHANGELOG.md` from `git log`.

## Usage
- `/generate-changelog` in Claude Code
- or `claude /generate-changelog --from v1.0.0 --to HEAD`

## What it does
1. Runs `git log --oneline --decorate` to get commit history  
2. Parses conventional commit prefixes (feat/fix/docs/refactor/test/chore)  
3. Groups changes by type, newest first  
4. Prepends to existing CHANGELOG.md or creates new  

## Output format (Keep a Changelog compatible)
```markdown
## [Unreleased]
### ✨ Features  
### 🐛 Fixes  
### 📝 Docs  
### 🔧 Maintenance  
```
