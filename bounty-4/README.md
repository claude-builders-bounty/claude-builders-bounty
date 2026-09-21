# Claude PR reviewer agent

## Setup

1. Copy `.claude/agents/pr-reviewer.md` into the repository being reviewed.
2. Put `bin/claude-review` on your `PATH`.
3. Ensure `claude` and `gh` are authenticated, then run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

For reproducible/offline diff injection, use `--diff-file patch.diff`; this bypasses `gh` but still invokes Claude Code. The reviewer is read-only and emits Summary, Identified risks, Improvement suggestions, and Low/Medium/High confidence.

`validate_cli.py` checks URL parsing and artifact structure without requiring Claude credentials. `samples/` contains two outputs prepared from real public PR diffs fetched through GitHub; they are examples, not claims of a live Claude Code execution in this environment.
