# PR Reviewer Agent

Command-line reviewer that inspects a GitHub pull request diff and emits structured Markdown that can be pasted into a PR comment.

## Usage

```bash
agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
agents/pr-reviewer/claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md
```

On Windows PowerShell, use:

```powershell
.\agents\pr-reviewer\claude-review.ps1 --pr https://github.com/owner/repo/pull/123
```

Offline fixture mode for tests or demos:

```bash
agents/pr-reviewer/claude-review \
  --pr https://github.com/example/project/pull/1 \
  --metadata-file agents/pr-reviewer/fixtures/sample_pr_metadata.json \
  --diff-file agents/pr-reviewer/fixtures/sample_pr.diff
```

## Output Sections

- Summary
- Changed Files
- Identified Risks
- Improvement Suggestions
- Testing Gaps
- Confidence Score
- Suggested GitHub Comment

## Real PR Examples

- [Review output for claude-builders-bounty #2582](examples/review-claude-builders-bounty-2582.md)
- [Review output for python/cpython #134126](examples/review-python-cpython-134126.md)

## Heuristics

The reviewer is intentionally deterministic and dependency-free. It parses the PR diff, summarizes changed files, detects whether tests were modified, and flags risky additions such as `eval`, shell execution, `innerHTML`, and destructive SQL.

This makes the tool easy to run from Claude Code, GitHub Actions, or a local shell before handing the generated Markdown to a human reviewer or an LLM for deeper analysis.
