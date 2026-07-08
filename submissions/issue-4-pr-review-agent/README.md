# Issue 4 PR Review Agent

This submission adds a Claude Code-friendly PR review agent and a dependency-free `claude-review` CLI that reviews a public GitHub pull request and returns a structured Markdown comment.

Use `AGENT.md` as the sub-agent instruction file, and use `claude-review` as the executable implementation for the CLI acceptance path.

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Optional authenticated mode:

```bash
GITHUB_TOKEN=ghp_... ./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

The generated Markdown includes:

- Summary of changes.
- Identified risks.
- Improvement suggestions.
- Confidence score: Low, Medium, or High.
- Evidence used from the GitHub API.

## Setup

1. Install Python 3.10 or newer.
2. Run `chmod +x claude-review`.
3. Run the CLI with a GitHub PR URL.
4. Optionally pass `GITHUB_TOKEN` for higher GitHub API limits.
5. Paste the generated Markdown as the structured review comment.
