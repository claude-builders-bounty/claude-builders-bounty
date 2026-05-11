# Claude Review PR Agent

`claude-review` is a small CLI agent that fetches a GitHub PR diff and returns a structured Markdown review comment.

It is intentionally dependency-light: Python 3 only, with optional `gh` CLI support for authenticated/private PRs.

## Setup

```bash
cp pr-review-agent/claude-review /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

Or run it directly from this repo:

```bash
./pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output format

The generated Markdown includes:

- Summary of changes in 2–3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## GitHub Action option

See `.github/workflows/claude-review.yml` for a workflow that posts the generated review comment on pull requests.
