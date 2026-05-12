# Generate Changelog

Generate a structured `CHANGELOG.md` from the current repository's git history.

Run:

```bash
bash changelog.sh
```

The command detects the latest git tag, reads commits after that tag, categorizes them as `Added`, `Fixed`, `Changed`, or `Removed`, and writes `CHANGELOG.md`.
