---
name: generate-changelog
description: Automatically generates a structured, Keep-a-Changelog compliant CHANGELOG.md from git history since the last tag.
---

# Generate Changelog Skill

Automatically inspects the repository's git commit log since the latest git tag, parses Conventional Commits prefixes (`feat:`, `fix:`, `refactor:`, `perf:`, `docs:`, `security:`), and categorizes them into standard Keep a Changelog sections:
- `Added`
- `Fixed`
- `Changed`
- `Removed`
- `Security`

## How to use

Run the generator script directly or invoke via Claude Code:

```bash
bash changelog.sh [VERSION]
```

Or with Python:
```bash
python3 generate_changelog.py 1.0.0
```

## Features
- **Tag-aware**: Detects the latest tag and only summarizes commits since that release.
- **Standards compliant**: Conforms strictly to [Keep a Changelog](https://keepachangelog.com).
- **Non-destructive**: Prepends new versions to existing `CHANGELOG.md` files without overwriting older release history.
- **Zero dependencies**: Uses Python 3 standard library only.
