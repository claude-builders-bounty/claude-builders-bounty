# Generate Changelog

1. Copy this folder into your Claude Code skills directory.
2. Run `bash scripts/changelog.sh` from any Git repository.
3. Review the generated `CHANGELOG.md` before committing it.

The script reads commits after the latest tag, categorizes them as Added, Fixed, Changed, or Removed, and writes an `Unreleased` section.
