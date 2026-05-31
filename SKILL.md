---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a user asks for `/generate-changelog` or wants a changelog generated from the current git repository.

## Steps

1. Run `python generate_changelog.py` from the repository root.
2. Review the generated `CHANGELOG.md` sections: Added, Fixed, Changed, Removed.
3. If the user specifies a range, pass it with `--since <tag-or-ref>`.

## Command

```bash
python generate_changelog.py
```

Optional:

```bash
python generate_changelog.py --since v1.0.0 --output CHANGELOG.md
```
