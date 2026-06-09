# Bounty #4 verification map

Maps each acceptance criterion to the exact command or artifact in this PR.

| Criterion | Evidence |
|-----------|----------|
| CLI: `claude-review --pr <url>` | Repo-root `./claude-review` and `agents/claude-review/claude_review.py` |
| GitHub Action workflow YAML | `agents/claude-review/.github/workflows/claude-review.yml` |
| Summary (2–3 sentences) | `build_narrative_summary()` + `format_markdown()` → **Summary of Changes** section |
| Identified risks (list) | **Identified Risks** with `HIGH` / `MEDIUM` / `LOW` severity tags |
| Improvement suggestions (list) | **Improvement Suggestions** section |
| Confidence score (Low/Medium/High) | **Confidence Score** section |
| Tested on ≥2 real GitHub PRs | `samples/review-brand-pr8.md`, `samples/review-bounty-pr2504.md`, `samples/review-bounty-pr2505.md` |
| README with setup and usage | `agents/claude-review/README.md` |

## Commands

```bash
# Unit tests (60 cases) + delivery verification (7 cases) + peer-review acceptance (18 cases) + CI guards
npm test
# or: bash agents/claude-review/tests/run-ci-checks.sh

# Live CLI against a public PR
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2504

# Offline review (no token)
git diff main...HEAD > /tmp/changes.diff
./claude-review --diff-file /tmp/changes.diff --title "local branch"
```

Expected test output ends with `Ran 60 unit tests — OK`, `Ran 7 delivery verification tests — OK`, `Ran 18 tests — OK`, `OK: peer review acceptance tests passed`, `OK: 85 tests passed`, and `OK: all CI validation checks passed`.

## Hands-on delivery (2026-06-09)

Peer-review recommendations addressed:

- URL-encode owner/repo segments in GitHub API paths
- Recompute line totals when `--max-files` truncates changed files
- Add invalid-token and API auth-failure regression tests
- Document fork-PR `--post` token limitation in README
- Codify hardened helper coverage in peer-review acceptance suite

Verified via `npm test` on branch `bounty-4-claude-review-agent` (PR #2533).
