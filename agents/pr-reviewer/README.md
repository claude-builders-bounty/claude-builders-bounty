# Claude PR Reviewer Agent

Generate a structured Markdown review from a GitHub pull request diff.

## Setup

```bash
chmod +x agents/pr-reviewer/claude-review
```

Optional:

```bash
ln -s "$PWD/agents/pr-reviewer/claude-review" /usr/local/bin/claude-review
```

## Usage

```bash
agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

If installed on your `PATH`:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Write to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output

The review is Markdown and includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## How It Works

The CLI fetches PR metadata and diff through GitHub CLI when available, with a
public GitHub HTTP fallback. It then performs deterministic static analysis over
the diff so it can run without an API key.

`AGENT.md` contains the Claude Code agent instructions if you want Claude to use
the same review contract with deeper project context.

## Validation

Sample outputs from two real GitHub PRs are included:

- `samples/claude-builders-bounty-1527.md`
- `samples/claude-builders-bounty-1528.md`
