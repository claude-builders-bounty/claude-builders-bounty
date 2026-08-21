# claude-review — Claude Code PR Reviewer Agent

A standalone agent that reviews a GitHub PR and emits a **structured Markdown
review**: summary, risks, improvement suggestions, and a confidence score.

Bounty #4 — powered by [Opire](https://opire.dev).

## Usage

```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

Requires either:
- `gh` CLI authenticated (`gh auth login`), **or**
- `--gh-token <TOKEN>` / `GH_TOKEN` env var

## Output format

```markdown
## 🤖 Automated PR Review — #123
### Summary
This PR touches N file(s) (X additions, Y deletions) in Lang×n. ...
### Identified Risks
- `snippet` — description
### Improvement Suggestions
- suggestion
### Confidence Score
High / Medium / Low
```

## How it works

1. Parses the PR URL → fetches the unified diff (gh CLI or REST API)
2. Splits the diff per file, computes stats (files, +/- lines, languages)
3. Scans **added code lines** against ~20 heuristic risk patterns:
   - Secrets: hardcoded keys, AWS AKIA IDs, `ghp_` tokens
   - Injection: `eval`/`exec`/`shell=True`/`os.system`/f-string SQL
   - Destructive: `DROP TABLE`, `TRUNCATE`, `DELETE FROM` w/o `WHERE`, `rm -rf`, `git push --force`
   - Path traversal, bare `except`, insecure options (`verify=False`, wide CORS)
4. Emits suggestions (large PR, missing tests, multi-language, etc.)
5. Computes a confidence score from diff size/scope/findings

**Noise control:** docstrings, comments, test-fixture strings, and regex
pattern definitions are skipped, so "documentation that *mentions* `rm -rf`"
does not produce false positives.

## Tested on real PRs

- `sample-1.md` — review of PR #3812 (a security hook PR; correctly flags the
  one real broad `except Exception` and nothing else)
- `sample-2.md` — review of PR #3786 (a clean agent PR; no findings, High confidence)

## Requirements

- Python 3.8+ (stdlib only)
- GitHub access: `gh` CLI or token

## License

MIT
