# Claude PR Review Agent ($150)

A Claude Code sub-agent that analyzes PR diffs and returns structured Markdown reviews.

## Usage

```bash
# Via PR URL
python claude-review.py --pr https://github.com/owner/repo/pull/123

# Via local diff file
python claude-review.py --diff pr.diff

# Via gh CLI pipe
gh pr view 123 --json body,title,files | python claude-review.py
```

## Output

```
# Review: fix: register-user-id (#2845)

## Summary of Changes
Reviews 2 file(s) across 1 type(s) (js). +32 / -4 lines.

## Identified Risks
### Medium Severity
- 🟡 `apps/api/src/services/authService.js`: Unresolved TODO

## Improvement Suggestions
*No specific suggestions — PR looks clean.*

## Confidence Score: **🟢 High**
Changes are well-scoped, tested, and clean.
```

## Features

- **Static analysis without an API key** — rule-based security checks (eval, XSS, SQLi, secrets, debuggers)
- **Dependency / config change detection** — flags package changes, config file modifications
- **Test coverage awareness** — flags missing test changes for non-trivial PRs
- **No external dependencies** — pure Python stdlib

## Requirements

- Python 3.8+
- `GITHUB_TOKEN` env var (optional, for higher API rate limits)
