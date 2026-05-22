# Claude PR Reviewer Agent

This agent generates a structured Markdown review for a GitHub pull request diff. It can run locally through the `claude-review` CLI or in GitHub Actions.

## Setup

No package install is required. The agent uses the Python standard library.

```bash
cd agents/pr-reviewer
chmod +x claude-review
```

For higher GitHub API rate limits or private repository access, set a token with pull request read access:

```bash
export GITHUB_TOKEN=your_github_token
```

## CLI Usage

Review a public GitHub pull request:

```bash
agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

Write the Markdown review to a file:

```bash
agents/pr-reviewer/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --output claude-pr-review.md
```

Review a local diff while still labeling the target PR:

```bash
agents/pr-reviewer/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --diff-file /path/to/pr.diff
```

## Output Contract

The generated Markdown contains:

- `Summary of Changes`
- `Identified Risks`
- `Improvement Suggestions`
- `Confidence Score: Low`, `Medium`, or `High`

The analyzer intentionally avoids private model or API dependencies. It scores the review from diff structure, touched file categories, change volume, and common risk signals such as workflow, dependency, test, and secret-adjacent path changes.

## GitHub Action

The included workflow example at `github-action/claude-review.yml` can run manually with a PR URL or automatically on pull request events after it is copied to `.github/workflows/claude-review.yml` in the target repository. It writes `claude-pr-review.md`, uploads it as an artifact, and posts the same Markdown as a PR comment when the Actions token has comment permission.

## Sample Outputs

Two real public PR runs are included:

- `samples/bottube-1151.md`
- `samples/rustchain-bounties-12023.md`

## Validation

```bash
python3 -m unittest discover -s agents/pr-reviewer/tests -v
python3 -m py_compile agents/pr-reviewer/claude_review.py agents/pr-reviewer/claude-review
```
