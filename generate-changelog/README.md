# Generate Changelog

`changelog.sh` generates a structured `CHANGELOG.md` from git commits since the latest tag, categorized into `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup

1. Run from any git repository: `bash generate-changelog/changelog.sh`
2. Optional: choose a range or output file with `--since v1.0.0` or `--output docs/CHANGELOG.md`
3. Commit the generated `CHANGELOG.md`

## Examples

```bash
bash generate-changelog/changelog.sh
bash generate-changelog/changelog.sh --stdout
bash generate-changelog/changelog.sh --since v1.0.0 --output RELEASE_NOTES.md
```

If the repository has no tags, the script uses all commits. It ignores merge commits and uses only Bash, Git, and standard Unix tools.
