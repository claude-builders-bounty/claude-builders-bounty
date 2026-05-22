# PR Reviewer Agent

`claude-review.py` is a small Claude Code helper that reviews a GitHub pull request diff and emits structured Markdown. It is designed for quick triage before a human review, with no external Python dependencies.

## Usage

Review a public GitHub PR:

```bash
python agents/pr-reviewer/claude-review.py --pr https://github.com/owner/repo/pull/123
```

Review a saved diff:

```bash
python agents/pr-reviewer/claude-review.py --diff-file path/to/pr.diff
```

Write the report to a file:

```bash
python agents/pr-reviewer/claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

The report always includes:

- Summary
- Risk assessment
- Suggested improvements
- Confidence score
- Review metadata

## Claude Code Agent

The sub-agent definition lives at `.claude/agents/pr-reviewer.md`. In Claude Code, ask the `pr-reviewer` agent to review a PR URL or local diff file. The agent runs this CLI and can refine the structured Markdown with additional context from the repository.

## Examples

Two reports generated from public GitHub PR URLs are included:

- `examples/pr-review-output-requests-7119.md`
- `examples/pr-review-output-flask-5808.md`

## Test

```bash
python agents/pr-reviewer/test_claude_review.py
```
