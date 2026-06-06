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
# Unit tests (39 cases)
python3 -m unittest agents/claude-review/tests/test_claude_review.py -v

# Live CLI against a public PR
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2504

# Offline review (no token)
git diff main...HEAD > /tmp/changes.diff
./claude-review --diff-file /tmp/changes.diff --title "local branch"
```

Expected test output ends with `OK` and `Ran 39 tests`.
