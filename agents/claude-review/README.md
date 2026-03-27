# claude-review

CLI tool that fetches a GitHub PR, extracts the diff and metadata, and runs it through Claude for a structured code review.

## Requirements

- `gh` CLI (authenticated)
- `claude` CLI
- `jq`

## Usage

```bash
# Full URL
claude-review --pr https://github.com/owner/repo/pull/123

# Shorthand
claude-review --pr owner/repo#123
```

## Output Format

Every review includes four sections:

- **Summary** -- 2-3 sentences on what the PR does
- **Risks** -- potential bugs, security issues, breaking changes
- **Suggestions** -- concrete improvements with file/line references
- **Confidence** -- Low / Medium / High based on how well the reviewer can assess the changes

## How It Works

1. Fetches PR metadata via `gh pr view` (title, body, files, stats)
2. Fetches the diff via `gh pr diff` (truncated to 3000 chars for large PRs)
3. Builds a structured prompt with the metadata and diff
4. Pipes it to `claude` CLI for analysis

## Limitations

- Diffs over 3000 characters are truncated. For very large PRs, the review may miss changes in later files.
- Requires the `claude` CLI to be configured and authenticated.
- Review quality depends on having enough context in the diff. Single-file changes get better reviews than sprawling refactors.

## Sample Outputs

See `sample-output-1.md` and `sample-output-2.md` for example reviews on real PRs.
