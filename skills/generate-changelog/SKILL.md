---
name: generate-changelog
description: Use when generating or updating a structured CHANGELOG.md from git history.
---

# Generate Structured Changelog

## Overview
This skill automatically inspects git commit history since the last git tag (or from the start of the repository) and generates or prepends an aligned `CHANGELOG.md` following the Keep a Changelog standard.

## Usage
Run the bundled changelog script from any repository root:

```bash
bash /path/to/changelog.sh
```

Optional parameters:
- `--since <tag|commit_hash>`: Target specific starting point
- `--output <path>`: Custom destination file (default: `CHANGELOG.md`)

## Features
- Conventional Commit parsing: `feat:` -> Added, `fix:` -> Fixed, `refactor:`/`perf:`/`chore:` -> Changed, `revert:`/`remove:` -> Removed.
- Deduplication and commit hash reference linkage.
- Preserves existing changelog records when prepending new unreleased or tagged sections.
