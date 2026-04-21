# Claude PR Review Agent

A lightweight Claude Code-style PR review agent that accepts a GitHub pull request URL, fetches the PR diff, analyzes it, and returns a structured Markdown review comment.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
claude-builders-bounty/claude-pr-review-agent/install.sh
```

Make sure `~/.local/bin` is on your `PATH`, then run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Optional Claude Code sub-agent setup:

```bash
mkdir -p ~/.claude/agents && cp pr-reviewer-agent.md ~/.claude/agents/pr-reviewer.md
```

You can also run it without installing:

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Output Format

The command prints Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## Examples

Sample outputs from two real GitHub PRs are included in `samples/`:

- `samples/fastapi-11000.md`
- `samples/pytest-12345.md`

## Local Diff Mode

For offline review or CI experiments:

```bash
claude-review --diff-file ./my-pr.diff
```

## Notes

The agent uses only the Python standard library and GitHub's public PR diff endpoint, so it does not require API keys for public repositories. For private repositories or higher rate limits, run it in an environment where GitHub requests are allowed and adapt `_github_headers()` to add an authorization token.
