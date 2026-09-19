# `claude-review`

`claude-review --pr https://github.com/owner/repo/pull/123` downloads a public
GitHub PR diff and returns a structured Markdown review containing a 2–3
sentence summary, risks, improvement suggestions, and a Low/Medium/High
confidence score.

When the Claude Code CLI is installed, the tool delegates the analysis to it.
Otherwise it uses a deterministic lightweight fallback so the CLI remains
usable in CI and produces a valid structured report.

## Setup

```bash
python3 -m pip install .
claude-review --pr https://github.com/owner/repo/pull/123
```

Or run directly without packaging:

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

The command only reads the public diff and writes the report to stdout.
