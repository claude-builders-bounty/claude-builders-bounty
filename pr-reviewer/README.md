# Claude Code PR Reviewer Agent

A CLI and GitHub Action that reviews a pull request diff and outputs a structured Markdown review comment.

It works in two modes:

1. **Claude-powered mode** — if `ANTHROPIC_API_KEY` is set, the diff is reviewed by Claude.
2. **Offline static-analysis fallback** — if no API key is configured, the agent still produces a useful structured review using deterministic heuristics.

## CLI usage

```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

Optional shell alias:

```bash
alias claude-review='python /path/to/pr-reviewer/claude-review.py'
claude-review --pr https://github.com/owner/repo/pull/123
```

## GitHub Action usage

Copy the workflow file into your repository:

```bash
mkdir -p .github/workflows
cp pr-reviewer/.github/workflows/claude-review.yml .github/workflows/claude-review.yml
```

Then add `ANTHROPIC_API_KEY` to repository secrets for Claude-powered reviews. Without the secret, the static-analysis fallback still runs.

## Output format

The agent always returns Markdown with:

- Summary of changes (2–3 sentences)
- Identified risks
- Improvement suggestions
- Confidence score (`Low`, `Medium`, or `High`)

## Example output

```markdown
## 🔍 Claude Code PR Reviewer Report

### 📝 Summary of Changes
Reviewing PR #123 - 'Add validation to upload endpoint'. This PR contains 87 additions across files. The description indicates: Adds upload validation and tests...

### ⚠️ Identified Risks
- Possible hardcoded secret or credential detected in source code.
- Large PR size: review is complex and edge cases may be missed.

### 💡 Improvement Suggestions
- Move secrets to environment variables or use a secret manager.
- Consider breaking the PR into smaller, modular pull requests.

**Confidence Score:** `Medium (Static Analysis)`
```

## Requirements

- Python 3.8+
- `gh` CLI for private repositories or reliable authenticated GitHub access
- Optional: `ANTHROPIC_API_KEY` for Claude-powered review
