---
name: generate_changelog
description: Generate a structured, semver-compliant CHANGELOG.md from git commit history following the Conventional Commits specification.
---

# Generate CHANGELOG Skill

This skill parses git commit history according to the [Conventional Commits specification](https://www.conventionalcommits.org/) and outputs a clean, structured [Keep a Changelog](https://keepachangelog.com/) formatted Markdown document.

## Features

- **Conventional Commit Parsing**: Automatically categorizes `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, and `chore` commits.
- **Breaking Change Detection**: Identifies breaking changes (`!:` or `BREAKING CHANGE:`) and highlights them at the top of the version section.
- **Scope Grouping**: Formats scoped commits (e.g. `feat(auth): add MFA`) with bold scope prefixes.
- **Commit Range & Tag Support**: Supports commit ranges (e.g. `v1.0.0..HEAD`) or full repository history.

## Usage

### 1. Execute via Python Script

```bash
python3 skills/generate_changelog/scripts/generate_changelog.py --version "v1.2.0" --output CHANGELOG.md
```

### 2. Generate for Specific Release Range

```bash
python3 skills/generate_changelog/scripts/generate_changelog.py --range "v1.1.0..HEAD" --version "v1.2.0"
```

## Output Format Example

```markdown
## [v1.2.0] - 2026-10-01

### ⚠️ BREAKING CHANGES
- **auth**: remove legacy session tokens (a1b2c3d)

### Features
- **user**: add multi-factor authentication support (e5f6g7h)

### Bug Fixes
- **db**: fix connection pool timeout on heavy load (i8j9k0l)

### Performance Improvements
- **cache**: implement LRU memory cache for user sessions (m1n2o3p)
```
