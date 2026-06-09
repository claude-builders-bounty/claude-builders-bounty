---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history with auto-categorization"
version: 1.0.0
author: Claude Builders Bounty
license: MIT
---

# Generate Changelog

Automatically generate a structured `CHANGELOG.md` from your project's git history.

## Usage

Run this skill:
```
/generate-changelog
```

Or with options:
```
/generate-changelog --tag v1.0.0 --name "My Project" --url https://github.com/user/repo
```

## Behavior

1. Fetches all commits since the last git tag
2. Categorizes by conventional commit prefix:
   - `feat:` / `add:` 鈫?**Added**
   - `fix:` 鈫?**Fixed**
   - `chore:` / `refactor:` / `docs:` 鈫?**Changed**
   - `remove:` / `deprecate:` 鈫?**Removed**
3. Writes a formatted `CHANGELOG.md` with commit hashes and optional links
4. Appends contributor stats

## Requirements

- Git repository with conventional commit messages
- At least one git tag (optional 鈥?works from beginning too)
