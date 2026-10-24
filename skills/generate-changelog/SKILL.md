---
name: generate-changelog
description: Automatically generates a production-grade, structured CHANGELOG.md from git history since the last tag following the Keep a Changelog standard.
---

# Generate Structured CHANGELOG

Autonomous skill that extracts Git commits, parses Conventional Commit types (`feat`, `fix`, `docs`, `perf`, `refactor`, `security`, `remove`), groups them into semantic categories (`Added`, `Fixed`, `Changed`, `Removed`, `Security`), attributes authors and commit hashes, and formats a clean `CHANGELOG.md`.

## When to Use
- When releasing a new version (`v1.0.0`, `v2.1.0`)
- When user asks to "generate changelog", "summarize recent commits", or "update CHANGELOG.md"
- Pre-release and CI/CD automated release notes workflows

## CLI Execution
```bash
python generate_changelog.py [version_tag]
# or via bash wrapper:
bash changelog.sh [version_tag]
```

## Categorization Standard
- `feat` / `feature` / `add` -> **Added**
- `fix` / `bugfix` / `hotfix` -> **Fixed**
- `refactor` / `update` / `change` -> **Changed**
- `remove` / `delete` -> **Removed**
- `security` -> **Security**
- `perf` / `performance` -> **Performance Improvements**
- `docs` -> **Documentation**
- `chore` / `ci` / `build` -> **Maintenance**
