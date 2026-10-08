---
name: generate-changelog
description: Generate a structured Keep-a-Changelog compliant CHANGELOG.md from git history, categorized into Added, Fixed, Changed, and Removed based on Conventional Commits and commit keywords since the last release tag.
---

# Git Changelog Generator Skill

A Claude Code skill and automated tool to inspect git commit history and produce standardized, categorized release notes.

## Invocation

This skill is invoked natively in Claude Code via:
```text
/generate-changelog
```

Or executed directly via Bash:
```bash
bash skills/generate-changelog/changelog.sh [OUTPUT_FILE] [RANGE]
```

## Features

- **Automatic Tag Detection**: Calculates commits between the latest git tag (`git describe --tags --abbrev=0`) and `HEAD`. If unversioned, analyzes initial release history.
- **Auto-Categorization**: Supports Conventional Commits and natural imperative git messages:
  - `Added`: New features and additions (`feat:`, `feat(...):`, `add:`, `added:`, `new:`, `Add `, `Create `, `Implement `)
  - `Fixed`: Bug fixes and security patches (`fix:`, `fix(...):`, `bugfix:`, `patch:`, `security:`, `Fix `, `Resolve `)
  - `Changed`: Improvements, refactoring, maintenance (`refactor:`, `perf:`, `chore:`, `style:`, `docs:`, `build:`, `ci:`, `test:`, `Update `, `Change `)
  - `Removed`: Deletions and deprecations (`remove:`, `removed:`, `revert:`, `deprecate:`, `Remove `, `Delete `)
- **Format Standard**: Strictly follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- **Robust Parsing**: Uses ASCII unit separators (`0x1f`) to safely handle pipe symbols (`|`), quotes, and special characters without delimiter corruption.
- **Zero Dependencies**: Requires only Bash and Git.

## Execution for Claude Code Agent

When this skill is invoked:
1. Locate the root of the current git repository (`git rev-parse --show-toplevel`).
2. Run `bash skills/generate-changelog/changelog.sh CHANGELOG.md`.
3. Read the generated `CHANGELOG.md` and present the categorized summary to the user.
