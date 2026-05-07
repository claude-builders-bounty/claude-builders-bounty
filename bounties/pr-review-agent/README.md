# claude-review

**Automated GitHub PR diff reviewer** — fetches a pull request diff via the GitHub API and outputs a structured Markdown review with a summary of changes, identified risks, and improvement suggestions.

## Features

- 🔍 Fetches PR metadata and diff via the **GitHub API** (no local git clone needed)
- 📋 Generates structured **Markdown review** with:
  - Summary of changes (2–3 sentences)
  - Files changed breakdown
  - Identified risks (secrets, security anti-patterns, general risks)
  - Improvement suggestions (code quality, recommendations)
- 🔐 Detects hardcoded secrets, API keys, tokens, and credentials
- 🛡️ Identifies security anti-patterns (XSS, SQL injection, command injection, etc.)
- 📝 Flags code quality issues (TODO/FIXME, debug logging, bare exceptions, etc.)
- 🔌 Works as a **CLI tool** or a **GitHub Action**
- 🐧 Linux/macOS — requires `bash`, `curl`, `python3` (stdlib only)

## Quick Start

### CLI Usage

```bash
# Using full PR URL
claude-review --pr https://github.com/owner/repo/pull/123

# Using PR number (auto-detects repo from git remote)
cd my-repo
claude-review --pr 123

# Explicit repo + PR number
claude-review --pr 42 --repo torvalds/linux

# With GitHub token (for private repos or higher rate limits)
claude-review --pr 123 --token ghp_xxxxxxxxxxxx

# Write output to file
claude-review --pr 123 --output review.md

# Using environment variable for token
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
claude-review --pr 123
```

### GitHub Action

Add `.github/workflows/claude-review.yml` to your repository:

```yaml
name: "PR Review (claude-review)"

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run claude-review
        id: review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sSL "https://raw.githubusercontent.com/YOUR_ORG/claude-review/main/claude-review.sh" \
            -o /usr/local/bin/claude-review
          chmod +x /usr/local/bin/claude-review
          claude-review \
            --pr "${{ github.event.pull_request.number }}" \
            --output /tmp/pr-review.md
          echo "review_file=/tmp/pr-review.md" >> $GITHUB_OUTPUT

      - name: Post review as PR comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('/tmp/pr-review.md', 'utf8');
            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });
            const existing = comments.find(c =>
              c.user.type === 'Bot' && c.body.includes('claude-review')
            );
            if (existing) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: existing.id,
                body: review,
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: review,
              });
            }
```

> **Note:** Replace `YOUR_ORG/claude-review` with the actual repository URL where you host the script.

## Install

### Option 1: Download directly

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/claude-review/main/claude-review.sh \
  -o /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

### Option 2: Clone the repository

```bash
git clone https://github.com/YOUR_ORG/claude-review.git
cd claude-review
sudo ln -s "$PWD/claude-review.sh" /usr/local/bin/claude-review
```

## Dependencies

- **bash** 4+ (or any POSIX-compatible shell)
- **curl** — for GitHub API requests
- **python3** — for diff parsing and analysis (stdlib only, no pip packages needed)

## How It Works

1. **Parses arguments** — extracts the repository slug and PR number from the provided URL or explicit `--pr`/`--repo` flags
2. **Fetches PR metadata** — calls `GET /repos/{repo}/pulls/{number}` with GitHub API v3 JSON endpoint
3. **Fetches the diff** — calls the same endpoint with `Accept: application/vnd.github.v3.diff` header
4. **Parses the diff** — splits into per-file chunks, counts additions/deletions
5. **Static analysis** — scans each added line for:
   - **Secrets & credentials**: API keys, tokens, private keys, passwords
   - **Security risks**: SQL injection, XSS, command injection, unsafe deserialization, etc.
   - **Code quality issues**: TODO/FIXME markers, debug logging, bare exceptions, large files
   - **Contextual risks**: CI/CD pipeline changes, database migrations, config file changes, Dockerfile changes
6. **Generates Markdown** — outputs a structured review with all findings

## Output Example

```markdown
# 🔍 PR Review: #123 — Add user authentication endpoint

> **Repository:** myorg/myapp
> **Author:** @developer
> **State:** open
> **Branch:** `main` ← `feature/auth`
> **Created:** 2025-05-08T03:23:00Z
> **Updated:** 2025-05-08T03:45:00Z

---

## 📋 Summary of Changes

This PR by **@developer** makes **12** file change(s) across **245** additions and **23** deletions. It targets the **`main`** branch from **`feature/auth`**. The description indicates: _Implements JWT-based authentication with login and registration endpoints._

...

## 🔴 Identified Risks

### Secrets & Credentials
  - ✅ No secrets detected.

### Security Anti-Patterns
  - ⚠️ **SQL injection risk — string concatenation in SQL query** in `src/users.py`
    ```text
    query = "SELECT * FROM users WHERE id = " + user_input
    ```

### General Risks
  - Database schema/migration `migrations/001_users.sql` changed — ensure backward compatibility and rollback plan.

...
```

## Authentication & Rate Limits

- **No token**: Works for public repos but is subject to GitHub's unauthenticated rate limit (60 requests/hour)
- **With token**: 5,000 requests/hour — set via `--token` or the `GITHUB_TOKEN` / `GH_TOKEN` environment variable
- **GitHub Actions**: Uses `secrets.GITHUB_TOKEN` automatically

## Limitations

- **Static analysis only** — does not execute code or run tests
- **Pattern-based** — detects known patterns but may produce false positives/negatives
- **No LLM integration** — analysis is heuristic, not AI-powered
- **Rate limited** — unauthenticated requests are limited to 60/hour

## Development

```bash
# Test locally
./claude-review.sh --pr https://github.com/rust-lang/rust/pull/123456

# Run with a specific token
./claude-review.sh --pr 42 --repo torvalds/linux --token ghp_xxx
```

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Pull requests welcome! Please open an issue first to discuss significant changes.

## Author

Created for the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) Opire bounty.
