# Claude PR review agent

This bounty deliverable adds a Claude Code-style PR review agent and a runnable CLI:

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

The command fetches the PR `.diff`, analyzes the changed files and patch content, and prints a structured Markdown review comment.

## Output format

The generated review contains:

- summary of changes in 2-3 sentences
- identified risks
- improvement suggestions
- confidence score: Low, Medium, or High

## Files

- `claude_review.py` - CLI implementation
- `pr-reviewer-agent.md` - Claude Code sub-agent prompt/instructions
- `sample_outputs/` - outputs from two real GitHub PRs

## Usage

```bash
python3 claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3401
```

Optional:

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Local validation

```bash
python3 claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3401
python3 claude_review.py --pr https://github.com/batotype/aba-quickplot/pull/2
```

The sample outputs in `sample_outputs/` were generated with those two real PR URLs.
