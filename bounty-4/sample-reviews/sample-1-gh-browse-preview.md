## PR Review: cli/cli#8001 — Add `gh browse --preview`

### Summary
This PR adds a `--preview` flag to the `gh browse` command that opens GitHub's rendered Markdown preview in the browser instead of the raw file. Changes are focused in `pkg/cmd/browse/browse.go` and associated test files.

### Risks
- **Low** — New flag is additive; no breaking changes to existing behavior.
- **Medium** — URL construction for preview endpoint differs between GitHub.com and GHES; may produce 404s on older GHES versions.

### Suggestions
1. Add a version check for GHES to fall back gracefully.
2. Expand test coverage for enterprise URLs.
3. Consider adding `--preview` to the shell completion definitions.

### Confidence
**High** — Small, well-scoped change with clear intent and good test coverage.
