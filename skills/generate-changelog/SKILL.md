---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog compliant CHANGELOG.md from git commit history since the most recent git tag.
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "update changelog"
---

# Generate Changelog Skill 📝

Analyzes git commits since the last release tag (or initial commit if untagged) and categorizes commits into standard [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) sections:
- **Added**: New features and capabilities (prefixes: `feat`, `add`, `feature`, `new`).
- **Fixed**: Bug fixes and issue resolutions (prefixes: `fix`, `bug`, `patch`, `resolve`).
- **Changed**: Modifications to existing functionality, refactoring, dependencies (prefixes: `refactor`, `perf`, `change`, `update`, `chore`).
- **Removed**: Deprecated or deleted features (prefixes: `remove`, `deprecate`, `rm`, `delete`).

## Usage

### In Claude Code / Agent CLI:
```bash
/generate-changelog
```

### Directly via Bash:
```bash
bash skills/generate-changelog/changelog.sh
```

### Directly via Python:
```bash
python skills/generate-changelog/generate_changelog.py
```
