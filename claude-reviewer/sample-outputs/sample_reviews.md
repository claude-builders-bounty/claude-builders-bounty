# Sample outputs — two real GitHub PRs

Both reports below were produced by the tool itself, unedited, with the static engine
(`ANTHROPIC_API_KEY` unset, no network beyond the public GitHub API):

```bash
python3 claude_review.py --pr https://github.com/pallets/flask/pull/6168
python3 claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4918
```

Sanity check of the two engines against the same input: the static report is the baseline,
the Claude engine enriches (never breaks) it. `python3 -m unittest discover -s . -p "test_*.py" -v`
passes 10/10 on Python 3.8-3.13.

---

## 1. `claude-builders-bounty/claude-builders-bounty#4918` — new feature (8 files, +759)

## Pull Request Review

**PR:** feat(agent): PR review CLI and GitHub Action with structured Markdown output | **URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4918

### Summary of Changes
This pull request (feat(agent): PR review CLI and GitHub Action with structured Markdown output) updates 8 file(s) (`agents/pr-reviewer/.github/workflows/claude-review.yml`, `agents/pr-reviewer/README.md`, `agents/pr-reviewer/action.yml` and 5 other file(s)) with +759 additions and -0 deletions. The patch encompasses 8 newly added file(s), 1 test file(s). Automated review flagged 2 high-severity and 1 medium-severity risk(s) that should be addressed before merging.

### Identified Risks
- **[High] Dynamic Code Execution** (`agents/pr-reviewer/bin/claude-review.mjs:47`): Use of dynamic code evaluation (`eval`/`exec`) can allow arbitrary code execution if untrusted input reaches this path.
- **[High] Hardcoded Secret / Credential** (`agents/pr-reviewer/test/analyze.test.mjs:72`): Potential hardcoded credential, API key, or secret token detected in source code.
- **[Medium] Large Patch Surface** (`agents/pr-reviewer/.github/workflows/claude-review.yml`): Large change set (+759/-0 lines across 8 files) increases review complexity and merge conflict risk.
- **[Low] Unresolved TODO / FIXME Marker** (`agents/pr-reviewer/src/analyze.mjs:9`): Unresolved `TODO`/`FIXME` marker introduced in the diff.
- **[Low] Unresolved TODO / FIXME Marker** (`agents/pr-reviewer/test/analyze.test.mjs:66`): Unresolved `TODO`/`FIXME` marker introduced in the diff.
- **[Low] Leftover Debug / Console Output** (`agents/pr-reviewer/test/analyze.test.mjs:72`): Debug statement or interactive breakpoint left in modified code.
- **[Low] Unresolved TODO / FIXME Marker** (`agents/pr-reviewer/test/analyze.test.mjs:72`): Unresolved `TODO`/`FIXME` marker introduced in the diff.

### Improvement Suggestions
- Replace `eval`/`exec` with safe parsers such as `json.loads`, `ast.literal_eval`, or explicit dispatch tables.
- Move sensitive credentials to environment variables (`os.environ` / `process.env`) and rotate any exposed keys immediately.
- Consider splitting independent refactors and feature additions into smaller, focused PRs.
- Resolve the deferred work item or link it to a tracked GitHub issue number.
- Remove leftover debug statements or replace them with structured logger calls before merging.

### Confidence Score
**Confidence Score: High** — High-severity security/reliability patterns were deterministically matched with exact line numbers.

---

## 2. `pallets/flask#6168` — maintenance change, merged upstream (12 files, +67/-433)

## Pull Request Review

**PR:** drop support for Python 3.10 | **URL:** https://github.com/pallets/flask/pull/6168

### Summary of Changes
This pull request (drop support for Python 3.10) updates 12 file(s) (`.github/workflows/tests.yaml`, `CHANGES.rst`, `docs/installation.rst` and 9 other file(s)) with +67 additions and -433 deletions. The patch encompasses 3 implementation module(s), 5 test file(s). Automated analysis found clean code changes with accompanying test coverage and no high-severity risks.

### Identified Risks
- **Low Risk:** No critical security, data-loss, or breaking API issues detected in the diff.

### Improvement Suggestions
- Verify all CI checks pass and consider adding edge-case assertions for boundary inputs.

### Confidence Score
**Confidence Score: High** — All 12 changed file(s) (+67/-433 lines) were completely parsed and analyzed against security and quality rules.

---

### What the two reports demonstrate

- **Risk detection with exact line numbers** — the first PR trips hardcoded-secret,
  `eval`, oversized-patch, `TODO` and debug-output rules on the real diff lines.
- **No false "high severity" on a clean patch** — the Flask PR is a multi-file
  compatibility change that correctly comes back clean, with test files present, so the
  missing-test rule stays silent and confidence stays `High`.
- **Stable output contract** — heading order, 2–3 sentence summary and the
  `**Confidence Score: High**` line are identical in both, which is what lets the GitHub
  Action drop the result straight into a PR comment.
