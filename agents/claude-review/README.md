# Claude Review Agent

`claude-review` fetches a GitHub PR diff and returns a structured Markdown review comment.

## Setup

```bash
python3 bin/claude-review --help
```

No third-party packages are required.

## Usage

```bash
python3 bin/claude-review --pr https://github.com/owner/repo/pull/123
python3 bin/claude-review --diff-file ./changes.diff --output review.md
python3 bin/claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

`--post-comment` uses `gh pr comment`, so it relies on the caller's existing GitHub CLI
authentication instead of storing tokens in this tool.

The output always includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Verification

```bash
python3 -m unittest discover -s tests
python3 -m py_compile bin/claude-review tests/test_claude_review.py
```

## Claude Code Sub-Agent

The `.claude/agents/pr-reviewer.md` file defines a Claude Code sub-agent prompt for deeper model-assisted review. Use the CLI for deterministic fetching and formatting, then hand the diff plus generated review to the sub-agent for refinement when needed.

## Samples

Two sample outputs generated from real public GitHub PR diffs are included in `samples/`:

- `samples/pr-61-review.md` from https://github.com/claude-builders-bounty/claude-builders-bounty/pull/61
- `samples/pr-92-review.md` from https://github.com/claude-builders-bounty/claude-builders-bounty/pull/92
