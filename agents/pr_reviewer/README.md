# PR Reviewer Agent

`claude-review` generates a structured Markdown review comment from a public
GitHub pull request diff.

## Setup

1. Use Python 3.9 or newer.
2. Run from this repository root, or copy `claude-review` and
   `agents/pr_reviewer/` into your tools repository.
3. Make the entry point executable on Unix-like systems with
   `chmod +x claude-review`.

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Or put the repository root on your `PATH` and run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

The generated comment contains:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

The `.claude/agents/pr-reviewer.md` file wraps this CLI as a Claude Code
sub-agent.
