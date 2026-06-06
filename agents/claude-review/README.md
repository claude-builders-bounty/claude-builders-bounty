# Claude Review

`claude-review` is a dependency-free CLI and Claude Code sub-agent wrapper that turns a GitHub pull request diff into a structured Markdown review.

## Setup

```bash
chmod +x agents/claude-review/claude-review
```

## Usage

```bash
agents/claude-review/claude-review --pr https://github.com/owner/repo/pull/123
```

The output includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Claude Code Agent

The sub-agent instructions live at:

```text
agents/claude-review/.claude/agents/claude-review.md
```

The agent delegates diff retrieval and first-pass analysis to the CLI, then returns the Markdown review.

## Real PR Samples

Sample outputs are included for two real PRs:

- `samples/claude-builders-bounty-2543.md`
- `samples/claude-builders-bounty-2544.md`

## Notes

The CLI uses public GitHub API endpoints and does not need external packages. It is intentionally deterministic so maintainers can run it in CI or locally without an LLM API key.
