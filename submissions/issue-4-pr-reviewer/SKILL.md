# Review a GitHub PR with Claude

Review any GitHub pull request and generate a structured Markdown report covering risks, suggestions, and a confidence score.

## Usage

```
/review-pr https://github.com/owner/repo/pull/123
/review-pr owner/repo/123
/review-pr owner/repo/123 --post-comment
```

## What you get

Claude will:
1. Fetch the PR diff and metadata from GitHub
2. Analyze the changes for risks, bugs, and improvements
3. Return a structured review with:
   - **Summary** (2–3 sentences)
   - **Identified Risks** (security, correctness, performance)
   - **Improvement Suggestions** (numbered, actionable)
   - **Confidence Score** (Low / Medium / High)

## Setup (one-time)

```bash
# 1. Set your API keys
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...   # needed for private repos + --post-comment

# 2. Copy the script somewhere on your PATH
cp ~/.claude/commands/review-pr/claude-review.py /usr/local/bin/claude-review.py
chmod +x /usr/local/bin/claude-review.py
```

## Steps

1. Ask the user for the PR URL if not provided.
2. Run: `python3 ~/.claude/commands/review-pr/claude-review.py --pr $PR_URL`
3. Present the Markdown review to the user.
4. If the user wants to post it as a GitHub comment, re-run with `--post-comment`.
5. Optionally save to file: `python3 claude-review.py --pr $PR_URL > review.md`

## Notes

- Works on any public GitHub PR without a token
- Private repos require `GITHUB_TOKEN` with `repo` scope
- Large PRs (>80 KB diff) are automatically truncated with a note
- Use `--json` flag for machine-readable output
- Use `--model claude-opus-4-5` for deeper analysis of complex PRs
