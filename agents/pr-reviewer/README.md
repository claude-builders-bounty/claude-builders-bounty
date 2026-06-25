# PR Reviewer Agent

`claude-review` fetches a GitHub pull request diff and returns a structured Markdown review comment.

## Setup

```bash
chmod +x claude-review scripts/claude_review.py
```

Optional, for private repos or posting comments:

```bash
export GITHUB_TOKEN=ghp_your_token
```

## Usage

Generate a review:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Write to a file:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post as a GitHub PR comment:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

## Output Shape

The generated Markdown includes:

- Summary of changes, 2 concise sentences
- Changed files
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

The companion sub-agent prompt lives at `agents/pr-reviewer/agent.md` for Claude Code workflows that prefer delegating the review prompt to an agent.
