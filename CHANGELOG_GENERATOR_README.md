# Generate Changelog Bounty

Generate a structured `CHANGELOG.md` from git history in 3 steps:

1. Copy `changelog.sh` into a git repository.
2. Run `bash changelog.sh` from the repository root.
3. Commit the generated `CHANGELOG.md`.

The script automatically detects the latest git tag, reads commits since that tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, then writes a formatted changelog.

See `SAMPLE_OUTPUT.md` for an example generated from a real GitHub repository.
