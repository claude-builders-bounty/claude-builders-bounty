# Claude review

`claude-review` creates a short Markdown review from a GitHub pull request diff.

It is designed for the bounty in issue #4:

- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- Claude Code agent prompt: `agents/pr-reviewer.md`
- Structured output with summary, risks, suggestions, and confidence

## Setup

The tool uses Python's standard library and the GitHub API. No package install is needed.

For private repos or higher rate limits:

```bash
export GITHUB_TOKEN=ghp_xxx
```

Run from the repository root:

```bash
python tools/claude_review/claude_review.py --pr https://github.com/owner/repo/pull/123
```

If `bin` is on your path, this also works:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## Output

The comment always uses this shape:

```markdown
## Summary

...

## Risks

- ...

## Suggestions

- ...

## Confidence

Medium
```

## Samples

Two real PR runs are included:

- `tools/claude_review/samples/projectdiscovery-nuclei-7158.md`
- `tools/claude_review/samples/claude-builders-bounty-1272.md`
