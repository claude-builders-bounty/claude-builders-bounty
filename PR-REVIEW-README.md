# Claude PR Review Agent

CLI and GitHub Action helper for the Claude Builders Bounty #4 task. It takes a GitHub PR diff, analyzes risk and test coverage, and returns a structured Markdown review comment.

## Install

```bash
python -m pip install -e .
```

After installation, the CLI entry point is available as:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

Review a public PR and print Markdown:

```bash
claude-review --pr https://github.com/python/cpython/pull/151541
```

Write the review to a file:

```bash
claude-review --pr https://github.com/python/cpython/pull/151541 --output review.md
```

Review a local diff:

```bash
claude-review --diff-file changes.diff
```

Use Claude CLI when available, with deterministic heuristic fallback:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --use-claude
```

Post the generated review as a GitHub PR comment:

```bash
GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

The default behavior is dry output only. The tool posts nothing unless `--post-comment` is explicitly passed.

## Output Format

The generated Markdown contains the required bounty sections:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

It also lists changed files to make the review easier to audit.

## GitHub Action

The workflow in `.github/workflows/claude-review.yml` can be triggered manually with a PR URL. It writes the Markdown review to the workflow summary, uploads it as an artifact, and can optionally post a PR comment when `post_comment` is set to `true`.

## Testing

Run the local unit tests:

```bash
python -m unittest discover -s tests
```

The tests cover URL parsing, diff parsing, required Markdown sections, risk detection, and confidence scoring.

## Sample Outputs

`samples/sample_outputs.md` contains outputs generated from two real public GitHub PRs:

- `https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2827`
- `https://github.com/python/cpython/pull/151541`

These samples satisfy the bounty requirement to include outputs from at least two real PRs.
