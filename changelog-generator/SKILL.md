---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history using conventional commits.
tags: [git, changelog, release, conventional-commits]
---

# Generate Changelog

Generates a structured `CHANGELOG.md` from git history, auto-categorizing conventional commits into **Added / Fixed / Changed / Removed**.

## Usage

```bash
# Generate changelog since last tag (stdout)
bash changelog-generator/changelog.sh

# With version label, write to file
bash changelog-generator/changelog.sh --version 1.0.0 --output CHANGELOG.md

# Prepend to existing changelog
bash changelog-generator/changelog.sh --version 1.0.0 --append --output CHANGELOG.md

# Link commits to GitHub
bash changelog-generator/changelog.sh --github owner/repo --output CHANGELOG.md
```

## How it works

1. Runs `git log` since the last tag (or `--since` ref)
2. Parses each commit subject as a conventional commit (`feat:`, `fix:`, `chore:`, etc.)
3. Maps types to categories: `feat` → Added, `fix` → Fixed, `refactor`/`chore` → Changed, `revert` → Removed
4. Formats as [Keep a Changelog](https://keepachangelog.com/) Markdown
5. Optionally links commit hashes to GitHub

## Conventional commit mapping

| Commit type | CHANGELOG category |
|-------------|-------------------|
| `feat`      | Added             |
| `fix`       | Fixed             |
| `perf`      | Changed           |
| `refactor`  | Changed           |
| `docs`      | Changed           |
| `chore`     | Changed           |
| `revert`    | Removed           |

Breaking changes (`feat!:` or `BREAKING CHANGE` in body) are highlighted with **BREAKING** prefix.

## Requirements

- Python 3.8+ (stdlib only, no dependencies)
- Git repository with conventional commits
