---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history, grouping commits by type and release range.
license: MIT
---

# Changelog Generator

Use this skill when you need to turn git commit history into a clean Markdown changelog.

## Quick use

```bash
python3 scripts/generate_changelog.py --since v1.0.0 --until HEAD --output CHANGELOG.md
```

If no range is provided, the script uses all reachable commits.

## Output format

The generated changelog groups commits into:

- Features
- Fixes
- Documentation
- Tests
- Refactors
- Maintenance
- Other

Each item includes the short commit hash and subject.
