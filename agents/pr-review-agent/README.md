# Claude PR Review Agent

Dependency-free CLI agent for bounty issue #4. It reads a GitHub pull request diff, analyzes the changed files, and emits a structured Markdown review comment with summary, risks, suggestions, and a Low/Medium/High confidence score.

The Claude Code sub-agent prompt lives in `claude-code-subagent.md`.

## Quick Start

1. Add the CLI to your PATH:

```bash
export PATH="$PWD/agents/pr-review-agent/bin:$PATH"
```

On Windows PowerShell:

```powershell
$env:Path = "$(Resolve-Path agents\pr-review-agent\bin);$env:Path"
```

2. Run a review:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

On Windows PowerShell, use:

```powershell
claude-review --pr https://github.com/owner/repo/pull/123
```

3. Or review a local diff without network access:

```bash
python agents/pr-review-agent/claude_review.py --diff-file path/to/change.diff
```

4. Save Markdown output:

```bash
python agents/pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123 --save review.md
```

5. Post the review as a PR comment:

```bash
GITHUB_TOKEN=ghp_xxx agents/pr-review-agent/bin/claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

6. Run tests:

```bash
python -m unittest tests/test_pr_review_agent.py
```

## Output Contract

The Markdown output always includes:

- `Summary of Changes`: 2-3 concise sentences as bullet points.
- `Identified Risks`: risk list based on diff shape, sensitive paths, missing tests, config changes, and change size.
- `Improvement Suggestions`: focused reviewer guidance.
- `Confidence`: `Low`, `Medium`, or `High`.

## Real PR Test Outputs

Included sample outputs:

- `sample-outputs/requestly-4718.md` from `https://github.com/requestly/requestly/pull/4718`
- `sample-outputs/claude-builders-bounty-1802.md` from `https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1802`

## Notes

- The agent uses only the Python standard library.
- Public PRs can be reviewed without a token because GitHub exposes `.diff` URLs.
- Posting a comment requires `GITHUB_TOKEN` with permission to comment on the target repository.
- The heuristics are deterministic. They are meant to give Claude Code or a human reviewer a clean first-pass review comment, not to replace maintainer review.
