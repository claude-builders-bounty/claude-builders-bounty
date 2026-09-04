# PR Review Agent Skill

## Description
A Claude Code agent that takes a PR diff as input, analyzes code changes, and posts a structured review comment. Works standalone via CLI or as a GitHub Action.

## Usage

### Via CLI (recommended)
```bash
# Review a PR by URL
bash skills/pr-review-agent/pr-review.sh https://github.com/owner/repo/pull/123

# Review a PR by owner/repo/number
bash skills/pr-review-agent/pr-review.sh owner/repo 123

# Output to file instead of posting
bash skills/pr-review-agent/pr-review.sh owner/repo 123 --dry-run > review.md

# Include file-by-file details
bash skills/pr-review-agent/pr-review.sh owner/rerepo 123 --verbose
```

### As GitHub Action
Add to `.github/workflows/pr-review.yml`:
```yaml
name: PR Review Agent
on:
  pull_request:
    types: [opened, synchronize]
permissions:
  pull-requests: write
  contents: read
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash skills/pr-review-agent/pr-review.sh "${{ github.repository }}" "${{ github.event.number }}"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Output Format

```markdown
## 📋 PR Review: #123 — Add user authentication

**Confidence:** 🟢 High | **Files Changed:** 5 | **Lines:** +142/-23

### Summary
2-3 sentence summary of what this PR does and why.

### ✅ Strengths
- What looks good

### ⚠️ Risks
- **[Severity]**: Description of each risk found

### 💡 Suggestions
- Actionable improvement suggestions

### 🔍 File-by-File Details
<details>
<summary>Click to expand</summary>

#### `src/auth.js` (+42/-3)
- Changes description
- Concern (if any)

</details>
```

## How It Works

1. **Fetches PR metadata** (title, body, changed files) via GitHub API
2. **Downloads the full diff**
3. **Analyzes** each file for:
   - Code complexity changes
   - Security patterns (auth, input validation, SQL injection, XSS)
   - Test coverage gaps
   - Performance concerns
   - Style consistency
4. **Calculates confidence score** based on:
   - 🟢 High: Small focused PR, familiar patterns, well-tested
   - 🟡 Medium: Moderate changes, some complexity
   - 🔴 Large/diffuse PR, unfamiliar domain, missing tests
5. **Outputs structured review** (posts to PR or stdout)

## Setup (3 steps)

1. **Copy this skill** into your project's `.claude/skills/` or `skills/` directory
2. **Ensure `gh` CLI is installed** and authenticated (`gh auth login`)
3. **Run**: `bash skills/pr-review-agent/pr-review.sh owner/repo PR_NUMBER`

## Dependencies
- `gh` CLI (>= 2.0)
- `jq` (for JSON processing)
- Standard Unix tools: `grep`, `sed`, `awk`
- GitHub token (via `GITHUB_TOKEN` env or `gh auth`)
