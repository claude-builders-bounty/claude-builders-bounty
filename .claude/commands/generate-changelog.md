# Generate Changelog

Generate a structured `CHANGELOG.md` from the current repository's git history.

Run this command from the repository root:

```bash
bash changelog.sh
```

The script fetches tags when an `origin` remote is available, finds commits since the latest reachable git tag, and writes the grouped changelog to `CHANGELOG.md`.

Optional output path:

```bash
bash changelog.sh --output RELEASE_NOTES.md
```
