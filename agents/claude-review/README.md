# claude-review — PR review agent

Takes a PR diff and returns a structured Markdown review.

## Usage

```bash
# Via PR URL
claude-review --pr https://github.com/owner/repo/pull/123

# Via local diff
claude-review --diff path/to/diff.patch
```

Requires `ANTHROPIC_API_KEY`. Uses `gh` CLI to fetch PR diffs.

## GitHub Action

See `claude-review.yml` for a ready-to-use workflow.

## Output

Structured Markdown: Summary, Identified risks, Improvement suggestions, Confidence score (Low/Medium/High).

## Sample

See `sample-output.md`.