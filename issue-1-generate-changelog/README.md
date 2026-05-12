# Generate Changelog

1. Run `bash issue-1-generate-changelog/changelog.sh /path/to/repo issue-1-generate-changelog/examples/CHANGELOG.sample.md`.
2. Review the generated Markdown grouped into `Added`, `Fixed`, `Changed`, and `Removed`.
3. Copy or move the output wherever you want to keep the project's `CHANGELOG.md`.

## Notes

- The script reads commits since the most recent git tag.
- If a repository has no tags yet, it falls back to the full commit history.
- Categorization is inferred from common commit prefixes like `feat:`, `fix:`, `remove:`, and everything else lands in `Changed`.
