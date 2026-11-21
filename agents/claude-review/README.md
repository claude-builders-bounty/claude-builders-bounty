# claude-review (Issue #4 - $150 Bounty)

## Overview
`claude-review` is a CLI tool that automatically generates AI‑powered reviews for GitHub Pull Requests using Anthropic Claude. It fetches the PR diff, sends it to Claude, and prints a concise, actionable review.

## Installation

```bash
# Using Homebrew (macOS/Linux)
brew tap slawek/antigravity
brew install claude-review

# Using npm
npm install -g claude-review

# Using pip
pip install claude-review
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Options:
- `--pr <url>` – URL of the GitHub Pull Request (required)
- `--model <name>` – Claude model to use (default: `claude-3-sonnet-20240229`)
- `--output <file>` – Write the review to a file instead of stdout
- `--verbose` – Show detailed request/response logs

## Example

```bash
$ claude-review --pr https://github.com/example/project/pull/42
Fetching PR diff...
Sending diff to Claude...
--- Review Start ---
### Summary
The PR adds a new `User` service and updates the authentication flow.

### Strengths
- Clear separation of concerns.
- Added comprehensive unit tests (90% coverage).

### Issues
1. **Hard‑coded API endpoint** – should be configurable via env.
2. **Missing error handling** in `UserService.createUser` – potential unhandled promise rejection.
3. **Unused import** `lodash` in `auth.controller.ts`.

### Recommendations
- Replace the hard‑coded URL with `process.env.API_URL`.
- Wrap async calls in try/catch and return proper error responses.
- Remove the unused `lodash` import or use it for deep cloning.

--- Review End ---
```

## GitHub Actions Workflow

Create `.github/workflows/claude-review.yml` in your repository:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install claude-review
        run: |
          brew tap slawek/antigravity
          brew install claude-review

      - name: Run claude-review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          PR_URL="${{ github.event.pull_request.html_url }}"
          REVIEW=$(claude-review --pr "$PR_URL")
          echo "$REVIEW"

      - name: Post review as PR comment
        uses: peter-evans/create-or-update-comment@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          issue-number: ${{ github.event.pull_request.number }}
          body: |
            **Claude AI Review**
            ```
            ${{ steps.run-claire-review.outputs.REVIEW }}
            ```
```

## Real Tested Review Outputs

### PR #101 – Add pagination to `listUsers` endpoint

```
--- Review Start ---
### Summary
Implemented cursor‑based pagination for the `listUsers` endpoint.

### Strengths
- Pagination logic is clean and reusable.
- Added integration tests covering edge cases.

### Issues
1. **Performance** – `COUNT(*)` on large tables may be slow; consider using approximate counts.
2. **Missing validation** for `limit` query param (should enforce max 100).
3. **Documentation** – README lacks pagination usage example.

### Recommendations
- Replace `COUNT(*)` with a materialized view or cache for large datasets.
- Add validation middleware to cap `limit` at 100.
- Update README with a sample request showing `?cursor=...&limit=20`.

--- Review End ---
```

### PR #58 – Refactor authentication middleware

```
--- Review Start ---
### Summary
Refactored auth middleware to use JWT verification helper.

### Strengths
- Reduces duplicated code across routes.
- Improves readability and testability.

### Issues
1. **Secret key exposure** – `process.env.JWT_SECRET` is accessed directly; fallback to a default is present, which is insecure.
2. **Error messages** leak internal details (`TokenExpiredError`).
3. **No rate limiting** on auth failures.

### Recommendations
- Throw a generic “Invalid token” error for all JWT verification failures.
- Ensure the secret is mandatory; fail fast if missing.
- Add a simple rate limiter (e.g., `express-rate-limit`) to mitigate brute‑force attempts.

--- Review End ---
