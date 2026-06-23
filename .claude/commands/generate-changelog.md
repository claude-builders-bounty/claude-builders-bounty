---
description: Generate CHANGELOG.md from git commits since the latest tag.
argument-hint: [output path]
---

Run the changelog generator from the repository root:

```bash
python tools/generate-changelog/generate_changelog.py ${ARGUMENTS:-CHANGELOG.md}
```

Then review the generated file for wording before committing it.
