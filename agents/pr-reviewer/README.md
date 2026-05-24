# Claude Code PR Reviewer Agent

> A Claude Code sub-agent that reviews GitHub pull requests and posts structured Markdown comments with analysis, risks, suggestions, and confidence scores.

## Features

- **CLI tool**: Review any PR from the command line
- **GitHub Action**: Automatically reviews PRs when opened/updated
- **Structured output**: Summary, risks, suggestions, and confidence score
- **Smart analysis**: References actual code from the diff
- **Updatable comments**: GitHub Action updates existing review on new pushes

## Quick Start

### CLI Usage

```bash
# Install
cd agents/pr-reviewer
npm install

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# Review a GitHub PR
node claude-review.mjs --pr https://github.com/owner/repo/pull/123

# Review a local diff file
node claude-review.mjs --diff changes.patch

# Pipe a diff
git diff | node claude-review.mjs
```

### Global CLI Install

```bash
npm link
claude-review --pr https://github.com/owner/repo/pull/123
```

### GitHub Action Setup

1. Copy `.github/workflows/pr-review.yml` to your repository
2. Add `ANTHROPIC_API_KEY` as a repository secret (Settings → Secrets → Actions)
3. Open a PR — the review will be posted automatically!

```yaml
# The action triggers on:
# - pull_request opened
# - pull_request synchronize (new commits pushed)
# - pull_request reopened
```

## Output Format

Every review follows this structure:

```markdown
# 🔍 PR Review: owner/repo#123
> https://github.com/owner/repo/pull/123

## 📋 Summary
(2-3 sentences describing the PR's purpose and scope)

## ⚠️ Risks
- Risk 1: Description with reference to specific code
- Risk 2: Description

## 💡 Suggestions
- Suggestion 1: Concrete improvement idea
- Suggestion 2: Another improvement

## 🎯 Confidence Score
**High** — Brief justification for the score
```

## Sample Outputs

### Sample 1: Simple Bug Fix PR

**Input PR:** A one-file change fixing an off-by-one error

```markdown
# 🔍 PR Review: acme/app#42
> https://github.com/acme/app/pull/42

## 📋 Summary
This PR fixes an off-by-one error in the pagination logic that caused the last page
of results to be empty when the total count was an exact multiple of the page size.
The fix is a single-line change adjusting the boundary check.

## ⚠️ Risks
No significant risks identified. The change is isolated to a single boundary condition
and the fix direction is correct.

## 💡 Suggestions
- Consider adding a unit test for the edge case where `totalCount % pageSize === 0`
  to prevent regression.
- The comment on line 15 could be updated to explain why `>=` is used instead of `>`.

## 🎯 Confidence Score
**High** — This is a small, well-understood fix with clear semantics. The change
correctly addresses the reported bug.
```

### Sample 2: New Feature PR (Auth Module)

**Input PR:** A multi-file PR adding OAuth2 authentication

```markdown
# 🔍 PR Review: acme/webapp#156
> https://github.com/acme/webapp/pull/156

## 📋 Summary
This PR adds OAuth2 authentication support for Google and GitHub providers.
It introduces a new auth middleware, token refresh logic, and user session
management across 8 files. The implementation follows the existing auth patterns
but adds significant new surface area.

## ⚠️ Risks
- **Token Storage (auth/storage.ts:34-45):** Tokens are stored in plain text in the
  session. Consider encrypting at-rest tokens or using a secure token store.
- **CSRF Protection (auth/callback.ts:12):** The OAuth callback doesn't validate the
  `state` parameter against the session, which could allow CSRF attacks.
- **Error Handling (auth/refresh.ts:67):** The token refresh silently fails and returns
  `null`, which could leave users in a broken authenticated state without clear feedback.
- **Rate Limiting:** No rate limiting on the `/auth/callback` endpoint, which could be
  abused for token brute-forcing.

## 💡 Suggestions
- Add the `state` parameter validation in the callback handler to prevent CSRF.
- Implement a token refresh retry mechanism with exponential backoff.
- Add structured error responses for auth failures instead of generic 500s.
- Consider adding logging/metrics for auth events (login, refresh, logout) for
  security auditing.
- Add integration tests for the full OAuth flow with mock providers.

## 🎯 Confidence Score
**Medium** — The core OAuth implementation is solid and follows standard patterns,
but the missing CSRF protection and plaintext token storage are security concerns
that should be addressed before merging. The feature works but needs hardening.
```

## Configuration

| Environment Variable | Required | Description |
|---------------------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `GITHUB_TOKEN` | For CLI | GitHub token (auto-set in Actions) |
| `GH_TOKEN` | For CLI | Alternative GitHub token |

## CLI Options

```
--pr <url>       GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
--diff <file>    Path to a diff/patch file
--model <model>  Claude model to use (default: claude-sonnet-4-20250514)
-h, --help       Show help message
```

## Requirements

- Node.js 18+
- Anthropic API key
- GitHub CLI (`gh`) installed and authenticated (for PR URL mode)

## License

MIT
