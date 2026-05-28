# Generate Changelog

Use this skill when the user asks to create or refresh a `CHANGELOG.md` from git history.

## Command

Run:

```bash
bash generate-changelog/changelog.sh --output CHANGELOG.md
```

## Behavior

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Reads commits after that tag, or all commits when no tag exists.
- Groups entries into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Markdown `CHANGELOG.md` with commit hashes for traceability.

## Notes

If the repository does not use conventional commits, the script falls back to keyword matching in commit subjects.
