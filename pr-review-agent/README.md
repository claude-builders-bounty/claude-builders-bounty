# 🔍 Claude PR Review Agent

A CLI tool and GitHub Action that uses Claude (via OpenRouter) to automatically review Pull Requests and post structured Markdown comments.

## Features

- **CLI tool**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Auto-runs on PR open/synchronize
- **Structured output**: Summary, risks, suggestions, confidence score
- **Fallback support**: OpenRouter primary, local Ollama fallback
- **Cost-effective**: Truncates large diffs to stay within token limits

## Setup

### CLI Usage

```bash
# 1. Clone and install
pip install requests  # if not already installed

# 2. Set API keys
export OPENROUTER_API_KEY=sk-or-v1-...
export GITHUB_TOKEN=ghp_...  # optional, for --post flag

# 3. Review a PR
./claude-review --pr https://github.com/owner/repo/pull/123

# 4. Save to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# 5. Post as GitHub comment
./claude-review --pr https://github.com/owner/repo/pull/123 --post
```

### GitHub Action

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - name: Run Claude Review
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python pr-review-agent/claude-review \
            --repo ${{ github.repository }} \
            --pr-number ${{ github.event.pull_request.number }} \
            --post
```

### Ollama Fallback (No API costs)

If OpenRouter credits run out, the tool automatically falls back to local Ollama:

```bash
ollama pull gemma4:latest  # or your preferred model
export OLLAMA_MODEL=gemma4:latest
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Format

Reviews follow a strict Markdown structure:

```markdown
# 🔍 PR Review: owner/repo#123

### Summary of Changes
What the PR does in 2-3 sentences.

### Identified Risks
- [HIGH] Potential SQL injection in user input
- [MEDIUM] Missing error handling for edge case
- [LOW] Unused import added

### Improvement Suggestions
- Use parameterized queries in `app.py:42`
- Add try/catch around file operations
- Remove unused `os` import

### Confidence Score
**Medium** — Changes are focused but touch security-critical code.

---
*Reviewed by Claude Code PR Review Agent*
```

## Test Results

### Test 1: [PR #1 on pokeehokee/test-repo](https://github.com/pokeehokee/test-repo/pull/1)

```markdown
# 🔍 PR Review: pokeehokee/test-repo#1

### Summary of Changes
This PR fixes a SQL injection vulnerability in the `get_user` function by switching from f-string query construction to parameterized queries. It also adds input validation to the `create_post` endpoint.

### Identified Risks
- [HIGH] Original code had direct string interpolation in SQL query (now fixed)
- [MEDIUM] No tests added for the new validation logic
- [LOW] `delete_post` returns inconsistent response format (dict vs None)

### Improvement Suggestions
- Add unit tests for `get_user` with edge cases (empty string, special chars)
- Consider using an ORM like SQLAlchemy instead of raw queries
- Standardize response format in `delete_post` to always return JSON

### Confidence Score
**High** — The fix is correct, minimal, and addresses the root cause directly.

---
*Reviewed by Claude Code PR Review Agent*
```

### Test 2: [PR #2 on pokeehokee/test-repo](https://github.com/pokeehokee/test-repo/pull/2)

```markdown
# 🔍 PR Review: pokeehokee/test-repo#2

### Summary of Changes
Adds JWT authentication middleware and protected routes for the blog API. Introduces `flask-jwt-extended` dependency.

### Identified Risks
- [HIGH] JWT secret key is hardcoded as `'dev-secret'` — must be environment variable
- [MEDIUM] Token expiry set to 30 days — consider shorter for security
- [MEDIUM] No rate limiting on `/login` endpoint (brute force risk)
- [LOW] Missing `@jwt_required()` on `delete_post` endpoint

### Improvement Suggestions
- Move `JWT_SECRET_KEY` to environment variable with fallback warning
- Reduce `JWT_ACCESS_TOKEN_EXPIRES` to 15 minutes, add refresh token flow
- Add `flask-limiter` to `/login` and `/register`
- Add `@jwt_required()` decorator to `delete_post`
- Consider adding token revocation/blacklist for logout

### Confidence Score
**Medium** — Authentication is correctly structured but security-critical configuration is hardcoded.

---
*Reviewed by Claude Code PR Review Agent*
```

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)
- OpenRouter API key (or Ollama for local fallback)
- GitHub token (only for `--post` flag)

## License

MIT
