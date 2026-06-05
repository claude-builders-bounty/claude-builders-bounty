# Claude Review Agent

`claude-review` is a small Claude Code-style PR review agent. It accepts a GitHub pull request URL, downloads the PR metadata and diff, and prints a structured Markdown review comment.

## Install

```bash
chmod +x claude-review-agent/claude-review
export PATH="$PWD/claude-review-agent:$PATH"
```

On Windows PowerShell, run the script through Python:

```powershell
python claude-review-agent/claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

For private repositories or higher GitHub API limits, set:

```bash
export GITHUB_TOKEN=ghp_your_token
```

## Output Format

The command prints Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## Test

```bash
python claude-review-agent/test_claude_review.py
```

## Sample Outputs

Two real PR sample outputs are included in:

- `samples/pr-2488-review.md`
- `samples/cli-cli-pr-13592-review.md`
