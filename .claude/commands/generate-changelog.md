# /generate-changelog

Generate a structured `CHANGELOG.md` from the current repository's git history.

Run:

```bash
bash changelog.sh
```

The command scans commits since the latest git tag, groups entries into `Added`, `Fixed`, `Changed`, and `Removed`, and writes `CHANGELOG.md`.
