---
name: generate-changelog
description: Automatically generates and updates a structured CHANGELOG.md following the Keep a Changelog standard from git commit history since the latest tag.
---

# Generate Structured Changelog

## Usage
Run `/generate-changelog` to analyze recent commits and update `CHANGELOG.md`.

## Execution
```bash
python generate_changelog.py
```

Categorizes commits into:
- **Added**: New features (`feat:`)
- **Fixed**: Bug fixes (`fix:`)
- **Changed**: Refactoring, performance, documentation (`refactor:`, `perf:`, `docs:`)
- **Removed**: Deprecations and removals (`remove:`, `deprecate:`)
