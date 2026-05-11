---
description: Generate CHANGELOG.md from commits since the latest git tag
argument-hint: "[--from <tag-or-ref>] [--output CHANGELOG.md]"
---

Run the repository changelog generator:

```bash
python3 changelog-generator/generate_changelog.py $ARGUMENTS
```

If no `--from` ref is provided, the script uses the latest reachable git tag. If the repository has no tags, it uses the first commit.
