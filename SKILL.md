---
name: generate-changelog
description: Generate structured CHANGELOG.md from git history
---

# Generate Changelog

Run `/generate-changelog` in Claude Code, or:

```bash
bash changelog.sh -o CHANGELOG.md
```

Examples:
- `bash changelog.sh` — commits since last tag
- `bash changelog.sh --since v1.0.0` — since a tag
- `bash changelog.sh --since 2025-01-01 --until 2025-03-31` — date range

Categories: feat→Added, fix→Fixed, refactor/perf→Changed, remove/revert→Removed, docs→Documentation, test→Tests, ci/build→CI
