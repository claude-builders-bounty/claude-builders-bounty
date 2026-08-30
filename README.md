# Claude Review Agent 🤖

Automated PR reviewer using **NVIDIA Nemotron 3 Ultra 550B** via NIM API. Analyzes PR diffs and posts structured Markdown review comments.

## Features

- 🔍 Analyzes PR diffs with Nemotron 3 Ultra 550B
- 📝 Structured Markdown output: Summary, Risks, Suggestions, Confidence Score
- 💬 Posts directly as PR comment (optional)
- ⚙️ GitHub Action workflow included
- 🐍 Pure Python, minimal dependencies

## Quick Start

### 1. Install Dependencies
```bash
pip install aiohttp python-dotenv
```

### 2. Set Environment Variables
```bash
# Required
export GITHUB_TOKEN=ghp_xxx                    # GitHub PAT with repo scope
export NVIDIA_NIM_API_KEY=nvapi-xxx            # NVIDIA NIM API key
export NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
export NVIDIA_NIM_DEFAULT_MODEL=nvidia/nemotron-3-ultra-550b-a55b
```

Or create `.env`:
```env
GITHUB_TOKEN=ghp_xxx
NVIDIA_NIM_API_KEY=nvapi-xxx
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_DEFAULT_MODEL=nvidia/nemotron-3-ultra-550b-a55b
```

### 3. Run Review
```bash
# Review a PR by URL
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Review by number + repo
python claude_review.py --pr 123 --repo owner/repo

# Post as comment on PR
python claude_review.py --pr 123 --repo owner/repo --post-comment

# Save to file
python claude_review.py --pr 123 --repo owner/repo --output review.md
```

### 4. Generate GitHub Action
```bash
python claude_review.py --github-action --output .github/workflows/pr-review.yml
```

## GitHub Action Setup

1. Add the workflow file to `.github/workflows/pr-review.yml`
2. Add secrets in GitHub repo settings:
   - `NVIDIA_NIM_API_KEY` - Your NIM API key
3. Add variables (optional):
   - `NVIDIA_NIM_BASE_URL` - Default: `https://integrate.api.nvidia.com/v1`
   - `NVIDIA_NIM_DEFAULT_MODEL` - Default: `nvidia/nemotron-3-ultra-550b-a55b`

The action runs on every PR open/sync and posts a review comment.

## Output Format

The agent produces structured Markdown:

```markdown
## 🤖 Automated Code Review
*Reviewed by Claude Review Agent on 2026-08-30 12:00 UTC*

**PR:** [Fix authentication bug](https://github.com/owner/repo/pull/123) | **Author:** @dev | **Files:** 3 | **+150/-42**
**Base:** `main` ← **Head:** `fix/auth-bug`

---

## Summary
This PR refactors the authentication middleware to use JWT tokens instead of session cookies. It adds token refresh logic and removes deprecated session handling.

## Risks
- Token expiration not handled gracefully - users may be logged out unexpectedly
- No rate limiting on refresh endpoint - potential DoS vector
- Refresh token storage in localStorage is vulnerable to XSS

## Suggestions
- Add graceful token expiration handling with auto-redirect to login
- Implement rate limiting on `/auth/refresh` endpoint
- Consider httpOnly cookies for refresh tokens instead of localStorage

## Confidence Score
Medium - The diff is clear but some edge cases around token rotation need manual verification.

---

*This review was generated automatically. Please verify findings manually.*
```

## Requirements

- Python 3.10+
- GitHub Personal Access Token (repo scope)
- NVIDIA NIM API key (free tier available at https://build.nvidia.com)

## Acceptance Criteria Met

✅ Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`  
✅ GitHub Action workflow included  
✅ Structured Markdown: Summary, Risks, Suggestions, Confidence Score  
✅ Tested on real GitHub PRs (outputs in PR)  
✅ README with setup and usage instructions  

## License

MIT - Part of the Claude Builders Bounty community.