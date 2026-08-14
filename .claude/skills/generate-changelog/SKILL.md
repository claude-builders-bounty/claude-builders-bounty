---
name: generate-changelog
description: Generate a structured CHANGELOG.md from commits since the latest git tag.
---

# Generate a changelog

Run the repository-local generator:

```bash
bash changelog.sh
```

The generator uses the newest tag as the boundary, categorizes commits into
Added, Fixed, Changed, and Removed, and writes `CHANGELOG.md`. Use
`python3 changelog.py --stdout` for a preview or `--from-tag v1.2.3` to select
an explicit boundary. Review the generated file before committing it.
