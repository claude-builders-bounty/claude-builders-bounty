# Claude PR Review Agent

A pure-bash CLI tool + GitHub Action that reviews GitHub Pull Requests and outputs structured Markdown analysis.

## Acceptance Criteria

✅ CLI: `claude-review --pr <url>`  
✅ GitHub Action included  
✅ Structured Markdown output (Summary, Risks, Suggestions, Confidence Score)  
✅ Works on real PRs (tested)  
✅ README with setup instructions  

## CLI Usage

```bash
# From PR URL
./claude-review --pr https://github.com/owner/repo/pull/123

# From PR number + repo
./claude-review --pr 456 --owner owner --repo repo --token ghp_xxxx

# Output to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Environment variable
export GITHUB_TOKEN=ghp_xxxx
./claude-review --pr 123 --owner owner --repo repo
```

### Output Format

```markdown
# 📋 PR Review — #123

**Repository:** owner/repo
**PR Title:** Fix login bug
**State:** open

## 📝 Summary
Description of changes

## ⚠️ Identified Risks
- SQL injection risk detected
- Empty catch block found

## 💡 Improvement Suggestions
- Add error handling
- Consider adding tests

## 📊 Confidence Score
[Medium]
```

## GitHub Action

See [`.github/workflows/pr-review.yml`](.github/workflows/pr-review.yml) — triggers on PR open/synchronize, posts review comment.

## Setup

```bash
chmod +x claude-review
# Set GITHUB_TOKEN env var or use --token
```

## Bounty

Closes #4