# claude-review

PR review agent that analyzes a GitHub pull request and generates a structured Markdown review.

## Setup

```bash
# Option 1: Direct CLI
chmod +x claude-review
./claude-review --pr https://github.com/owner/repo/pull/123

# Option 2: With token for private repos
GITHUB_TOKEN=your_token ./claude-review --pr https://github.com/owner/repo/pull/123

# Option 3: GitHub Action (see review-pr.yml)
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
claude-review --pr 123 --repo owner/repo
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## Output

The review includes:

- **Summary** — 2-3 sentence overview of changes
- **Risks** — Security issues, destructive operations, hardcoded secrets (High/Medium/Low)
- **Improvement Suggestions** — Code quality, patterns, maintainability
- **Confidence Score** — High (no issues), Medium (concerns), Low (high-severity risks)

## What it detects

| Category | Examples |
|----------|----------|
| Code injection | `eval()`, `exec()`, `os.system()`, `shell_exec()` |
| SQL injection | String concatenation in queries |
| XSS | `innerHTML`, `dangerouslySetInnerHTML` |
| Hardcoded secrets | `password = "..."`, `api_key = "..."` |
| Destructive operations | `rm -rf`, `DROP TABLE`, `DELETE FROM` without WHERE |
| Security | `git push --force`, `.env` references |
| Code quality | Deep nesting, bare except, console.log in prod |
| Maintainability | Complex functions, promise chains, deep imports |

## Requirements

- Python 3.6+
- No external dependencies (uses only stdlib)
- GitHub token for private repos (optional, uses `GITHUB_TOKEN` env var)

## Sample Output

See `SAMPLE_OUTPUT_1.md` and `SAMPLE_OUTPUT_2.md` for real reviews of GitHub PRs.
