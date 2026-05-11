# Claude PR Review Agent

This folder contains a Claude Code project subagent and a standalone CLI for reviewing GitHub pull requests.

The main command is:

```bash
agents/pr-review/claude-review --pr https://github.com/owner/repo/pull/123
```

It fetches PR metadata and the unified diff, analyzes the changed files, and prints a structured Markdown review comment with:

- A 2 to 3 sentence summary
- Identified risks
- Improvement suggestions
- A Low, Medium, or High confidence score

## Setup

From the repository root:

```bash
chmod +x agents/pr-review/claude-review
ln -sf "$PWD/agents/pr-review/claude-review" /usr/local/bin/claude-review
```

If `/usr/local/bin` is not writable, run the script directly from the repo:

```bash
agents/pr-review/claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

Print a review comment to stdout:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Save the review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the review as a PR comment:

```bash
GITHUB_TOKEN=ghp_your_token claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

The token needs permission to read the PR and write issue comments in the target repository. Public PRs can usually be reviewed without a token, but unauthenticated GitHub API requests are rate limited.

## Claude Code Subagent

The project-level subagent lives at:

```text
.claude/agents/pr-reviewer.md
```

In Claude Code, invoke it with a request like:

```text
Use the pr-reviewer subagent to review https://github.com/owner/repo/pull/123
```

The subagent runs the CLI, inspects the output, and keeps the review in the required Markdown structure.

## Heuristics

The CLI combines PR metadata with diff inspection. It raises risk for:

- Source changes without matching test changes
- Dependency manifest or lockfile edits
- Auth, security, permission, or token-handling paths
- Database schema or migration changes
- CI workflow edits
- Environment or deployment configuration changes
- Large diffs that are hard to review safely

These heuristics are intentionally conservative. They are designed to produce a useful first-pass review that Claude Code can refine with project-specific context.

## Sample Outputs

Two real GitHub PR sample outputs are included:

- `sample-outputs/claude-builders-bounty-pr-889.md`
- `sample-outputs/claude-builders-bounty-pr-870.md`

Regenerate them with:

```bash
agents/pr-review/claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/889 --output agents/pr-review/sample-outputs/claude-builders-bounty-pr-889.md
agents/pr-review/claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/870 --output agents/pr-review/sample-outputs/claude-builders-bounty-pr-870.md
```

## Tests

Run the unit tests from the repository root:

```bash
python3 agents/pr-review/tests/test_claude_review.py
```

