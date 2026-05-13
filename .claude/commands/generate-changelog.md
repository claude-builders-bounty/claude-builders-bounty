# /generate-changelog

Generate a structured `CHANGELOG.md` from commits since the latest git tag.

Run this from the repository root:

```bash
bash changelog.sh
```

Use an explicit range or output path when needed:

```bash
bash changelog.sh --range v1.0.0..HEAD --output CHANGELOG.md
```
