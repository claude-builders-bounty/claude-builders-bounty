# Claude Review Agent

CLI and GitHub Action workflow that turns a GitHub PR diff into a structured Markdown review comment.

## Setup

```bash
chmod +x agents/claude-review/claude-review
```

Optional environment:

- `ANTHROPIC_API_KEY`: when set, use your Claude wrapper around the generated prompt.
- `GITHUB_TOKEN`: used by `gh` or GitHub Actions for private repositories and posting comments.

## CLI Usage

```bash
agents/claude-review/claude-review --pr https://github.com/owner/repo/pull/123
```

To post the generated review:

```bash
agents/claude-review/claude-review --pr https://github.com/owner/repo/pull/123 --post
```

The default implementation is deterministic and dependency-free. It fetches metadata and diff through `gh`, computes review heuristics, and emits the required Markdown sections:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

## GitHub Action

Copy `.github/workflows/claude-review.yml` into a repository. The action runs on pull requests and posts a structured review comment.

