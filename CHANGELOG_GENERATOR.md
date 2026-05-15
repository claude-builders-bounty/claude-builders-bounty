# Changelog Generator

Generate a structured `CHANGELOG.md` from git history in 3 steps:

1. Run `bash scripts/changelog.sh` from a git repository root.
2. Review the generated `CHANGELOG.md` sections: `Added`, `Fixed`, `Changed`, and `Removed`.
3. Commit the script and generated changelog when the output looks right.

The script automatically uses commits since the latest git tag. Use `--since <ref>` to override the range, or `--output <file>` to write somewhere other than `CHANGELOG.md`.
