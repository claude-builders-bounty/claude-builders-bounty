# Generate Changelog

Use this skill when the user asks to generate, refresh, or summarize a project changelog from git history.

## Workflow

1. Run `bash scripts/changelog.sh --dry-run` from the repository root to preview commits since the latest tag.
2. Run `bash scripts/changelog.sh --output CHANGELOG.md` to write the changelog.
3. Review the generated `Added`, `Fixed`, `Changed`, and `Removed` sections before committing.

## Notes

- The script uses the latest git tag as the default starting point.
- Pass `--since <tag-or-ref>` when a project needs a custom release boundary.
- Conventional commit prefixes are used first, with keyword fallback for non-conventional history.

