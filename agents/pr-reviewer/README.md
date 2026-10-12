# Claude Code PR Reviewer Agent 🤖

An automated, opinionated Pull Request reviewer designed for Claude Code and GitHub Actions. Analyzes PR diffs, flags operational risks, detects credential exposures, suggests architectural improvements, and scores merge confidence.

```
                  GitHub Pull Request (URL or Diff)
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │  claude_review.py CLI     │
                    │  ───────────────────────  │
                    │  • Diff Tokenizer & Stats │
                    │  • Destructive Heuristics │
                    │  • Secret / Credential Rx │
                    │  • Test Coverage Scoring  │
                    └─────────────┬─────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       [ Structured Markdown ]           [ JSON API Output ]
       • Summary of Changes              • --format json
       • 🚨 Identified Risks             • CI / CD Pipelines
       • 💡 Actionable Suggestions
       • 🎯 Confidence Score
```

---

## ⚡ CLI Usage

### Direct Pull Request URL Inspection:
```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```
Or via the bundled `claude-review` executable:
```bash
./agents/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

### Local Diff File Inspection (Offline Mode):
```bash
python3 agents/pr-reviewer/claude_review.py --diff-file /path/to/feature.diff
```

### Export Formats:
```bash
# Export Markdown
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Export Structured JSON
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --format json
```

---

## 🚀 GitHub Action CI Workflow

Drop `.github/workflows/claude-pr-review.yml` into your repository. On every PR open or update, the agent posts an automatic review directly to the conversation timeline.

---

## 📊 Evaluation Metrics

1. **Summary of Changes:** Invariant diff delta (+/- lines, file breadth).
2. **Identified Risks:** Destructive command patterns (`rm -rf`, `DROP TABLE`, `git push --force`), credential leakage.
3. **Actionable Suggestions:** Test file pairing, conventions.
4. **Confidence Score:** `Low` / `Medium` / `High` dynamically weighted against changeset radius.

Verified examples on live PRs:
- `examples/review_pr4791.md` (Tested on PR #4791)
- `examples/review_pr4792.md` (Tested on PR #4792)

---

## 🧪 Testing

```bash
python3 test_pr_reviewer.py
```
*(6/6 unit tests passing)*
