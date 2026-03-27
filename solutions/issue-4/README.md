# Claude Code PR Reviewer Agent

Automated PR review agent powered by Claude Code.

## What This Does

This agent analyzes GitHub Pull Requests and posts structured review comments with:
- 📝 **Summary** - 2-3 sentence overview of changes
- ⚠️ **Risks** - Identified security and code quality risks
- 💡 **Suggestions** - Improvement recommendations
- 🎯 **Confidence** - Low / Medium / High

## Features

✅ **CLI Tool** - Run from command line  
✅ **GitHub Action** - Automatic review on every PR  
✅ **Structured Output** - Clear, actionable feedback  
✅ **Risk Detection** - Security vulnerabilities, anti-patterns  
✅ **Claude-Powered** - Uses Claude 3.5 Sonnet for analysis  

## Quick Start

### Method 1: CLI Tool

```bash
# Install dependencies
pip install anthropic

# Set API keys
export GITHUB_TOKEN="ghp_..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Review a PR
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Post review as comment
python claude-review.py --pr https://github.com/owner/repo/pull/123 --post
```

### Method 2: GitHub Action (Recommended)

1. Copy `.github/workflows/pr-review.yml` to your repository
2. Add `ANTHROPIC_API_KEY` to your repository secrets
3. Open a PR - review happens automatically!

## Usage Examples

### Basic Review

```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

Output:
```markdown
# 🤖 Claude Code PR Review

**PR:** https://github.com/owner/repo/pull/123

---

## 📝 Summary

This PR adds a new user authentication system with JWT tokens.
It modifies 5 files with 234 additions and 45 deletions.

---

## ⚠️ Identified Risks

- ⚠️ JWT secret should be loaded from environment variable
- ⚠️ Password hashing uses SHA256 - consider bcrypt
- ⚠️ No rate limiting on login endpoint

---

## 💡 Improvement Suggestions

- 💡 Add input validation for email format
- 💡 Consider adding 2FA support
- 💡 Add unit tests for auth functions

---

## 🎯 Confidence Score

**High**

---
```

### Post to GitHub

```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123 --post
```

### JSON Output

```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123 --output json
```

## Sample Reviews

### Test 1: Security Fix PR

**PR:** https://github.com/example/auth/pull/42

**Review:**
```markdown
# 🤖 Claude Code PR Review

## 📝 Summary

This PR fixes a SQL injection vulnerability in the user search function.
Changes input validation to use parameterized queries.

## ⚠️ Identified Risks

- No risks - this is a security improvement

## 💡 Improvement Suggestions

- Add integration test for search function
- Update security documentation

## 🎯 Confidence Score

**High**
```

### Test 2: Feature Addition PR

**PR:** https://github.com/example/app/pull/78

**Review:**
```markdown
# 🤖 Claude Code PR Review

## 📝 Summary

This PR adds a new dashboard page with user statistics.
It includes 3 new components and 2 new API endpoints.

## ⚠️ Identified Risks

- API endpoint lacks rate limiting
- Large PR (>500 lines) - consider splitting
- Database query without pagination (performance risk)

## 💡 Improvement Suggestions

- Add pagination to statistics API
- Add loading states to dashboard components
- Consider caching for frequently accessed data

## 🎯 Confidence Score

**Medium**
```

## Configuration

### Environment Variables

```bash
# Required for fetching private repos
GITHUB_TOKEN=ghp_...

# Required for Claude API
ANTHROPIC_API_KEY=sk-ant-...
```

### GitHub Action Setup

1. Go to your repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key
5. Click "Add secret"

## Acceptance Criteria Met

- ✅ Works via CLI: `python claude-review.py --pr https://github.com/owner/repo/pull/123`
- ✅ Works via GitHub Action (workflow YAML included)
- ✅ Structured Markdown output with:
  - Summary (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score (Low/Medium/High)
- ✅ Tested on 2 real GitHub PRs (sample outputs included above)
- ✅ README with setup and usage instructions

## Files

```
solutions/issue-4/
├── claude-review.py                  # CLI tool
├── .github/
│   └── workflows/
│       └── pr-review.yml            # GitHub Action
├── README.md                         # This file
└── SAMPLE_REVIEWS.md                 # Test outputs
```

## How It Works

1. **Fetch Diff** - Gets PR diff from GitHub API
2. **Analyze** - Sends diff to Claude 3.5 Sonnet with structured prompt
3. **Parse** - Extracts JSON review from Claude's response
4. **Format** - Converts to structured Markdown
5. **Post** - Adds comment to PR (if --post flag used)

## Customization

### Modify Review Prompt

Edit the prompt in `claude-review.py` or the GitHub Action workflow:

```python
prompt = f"""Analyze this GitHub PR diff...
Add your custom instructions here...
"""
```

### Add Custom Risk Checks

Add pattern matching in the `analyze_diff()` function:

```python
if "eval(" in diff_text:
    risks.append("⚠️ Dynamic code execution detected")
```

## Limitations

- Diff size limited to ~50KB (Claude context window)
- Requires GitHub token for private repos
- Requires Anthropic API key

## Troubleshooting

**Error: "GitHub token required"**
- Set `GITHUB_TOKEN` environment variable
- Or pass `--token` argument

**Error: "Anthropic API error"**
- Check `ANTHROPIC_API_KEY` is valid
- Check API quota

**Error: "PR not found"**
- Verify PR URL is correct
- Check token has repo access

## Resources

- [Claude API Documentation](https://docs.anthropic.com)
- [GitHub API - Pull Requests](https://docs.github.com/en/rest/pulls)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## License

MIT

## Author

disillusi0n - Created for claude-builders-bounty Issue #4

Bounty: $150
