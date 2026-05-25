---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# /generate-changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## Usage

In the chat, type:

```
/generate-changelog
```

Or with a specific path:

```
/generate-changelog path=/path/to/repo
```

## How it works

1. Detects the last git tag as the version anchor
2. Fetches all commits since that tag
3. Categorizes by conventional-commit prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `chore:`, `refactor:`, `perf:` → **Changed**
   - `remove:`, `deprecat:` → **Removed**
4. Strips prefixes from commit messages
5. Writes `CHANGELOG.md` to the project root

## Requirements

- `git` installed and available on PATH
- The target directory must be a git repository
- Works best with conventional commit messages
