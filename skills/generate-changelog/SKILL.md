---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Supports conventional commits, Keep a Changelog format, and tag-based versioning.
---

# generate-changelog

Generate a structured `CHANGELOG.md` from git history.

## When to use

- User asks "generate changelog", "create CHANGELOG", or "document changes"
- After a release/tag, to document what changed
- When onboarding a new contributor who wants to see project history

## How it works

Runs `bash changelog.sh` from the `scripts/` directory.

Features:
- Parses conventional commits (feat:, fix:, refactor:, chore:, perf:, docs:, style:, test:)
- Auto-categorizes: Added / Fixed / Changed / Removed
- Supports `--stdout` for piping and `--since=<tag>` for custom ranges
- Keep a Changelog format compliant
- Zero dependencies (pure bash + git)

## Usage

```bash
# Generate CHANGELOG.md in current dir
bash scripts/changelog.sh

# Output to stdout (for piping)
bash scripts/changelog.sh --stdout

# Generate since specific tag
bash scripts/changelog.sh --since=v1.0.0
```

## Output format

Follows [Keep a Changelog 1.0.0](https://keepachangelog.com/en/1.0.0/) standard.
