# pr-review-agent — `claude-review`

A Claude Code agent / CLI that reviews a GitHub pull request and returns a
**structured Markdown review** (summary, risks, suggestions, confidence) — no
LLM API key required. It fetches the PR metadata and diff via the GitHub REST
API and runs deterministic static heuristics.

## Usage
```bash
# Via CLI
python claude-review.py --pr https://github.com/owner/repo/pull/123
python claude-review.py --pr owner/repo#123 --token $GITHUB_TOKEN
python claude-review.py --pr 123 -r owner/repo

# As a GitHub Action (see .github/workflows/review.yml)
```

Auth: set `GITHUB_TOKEN` (or `GITHUB_PAT`); public PRs work unauthenticated
(rate-limited).

## Output (Markdown)
- **Summary** — 2–3 sentence overview.
- **Identified risks** — large diffs, missing tests, committed secrets,
  dangerous APIs (`eval`/`exec`/`subprocess shell=True`/`pickle`/`yaml.load`),
  SQL string-concatenation, TODO/FIXME, schema migrations, dependency changes,
  breaking changes.
- **Improvement suggestions** — concrete next steps.
- **Confidence** — Low / Medium / High based on diff size and signal strength.

## Heuristics (deterministic, no model)
| Signal | Why it matters |
| --- | --- |
| Diff size / file count | Large changes hide defects |
| Missing tests | Regressions go unnoticed |
| Secrets in diff | Credential leakage |
| Dangerous APIs | RCE / injection surface |
| SQL concatenation | SQL injection |
| TODO/FIXME | Unfinished work merged |
| Schema migration | Backward-compat / rollback |
| Dependency changes | CVEs / license risk |

## GitHub Action
`.github/workflows/review.yml` runs `claude-review` on `pull_request` events
and posts the Markdown as a comment. See the file for setup.
