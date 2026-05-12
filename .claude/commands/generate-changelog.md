# Generate Changelog

Run the changelog generator from the repository root:

```bash
bash changelog.sh
```

The command writes a structured `CHANGELOG.md` from commits since the latest git tag. If the repository has no tags, it uses the full commit history.

