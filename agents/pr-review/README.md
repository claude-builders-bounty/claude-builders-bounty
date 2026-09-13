# claude-review

CLI + GitHub Action + Claude Code skill that reviews a pull request and emits **structured Markdown**:

1. Summary of changes (2–3 sentences)
2. Identified risks (list)
3. Improvement suggestions (list)
4. Confidence score: Low / Medium / High

## CLI

```bash
python3 agents/pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123
python3 agents/pr-review/claude_review.py --repo owner/repo --pr-number 123 --output review.md
```

Requires [GitHub CLI](https://cli.github.com/) (`gh`). Public repos work with any authenticated `gh` session.

## GitHub Action

Copy `action.yml` into `.github/workflows/claude-review.yml` (or reference this folder). It posts the structured review as a PR comment on every `pull_request` event.

## Claude Code skill

See `SKILL.md`. Install into your skills directory and ask Claude to review a PR URL.

## Sample outputs (real PRs)

- [`sample-output-1.md`](sample-output-1.md) — [cli/cli#14373](https://github.com/cli/cli/pull/14373) (docs-only, confidence High)
- [`sample-output-2.md`](sample-output-2.md) — [pallets/flask#5660](https://github.com/pallets/flask/pull/5660) (session refactor, confidence Medium)

Regenerate:

```bash
python3 agents/pr-review/claude_review.py --pr https://github.com/cli/cli/pull/14373 --output agents/pr-review/sample-output-1.md
python3 agents/pr-review/claude_review.py --pr https://github.com/pallets/flask/pull/5660 --output agents/pr-review/sample-output-2.md
```

## Confidence heuristic

| Score | When |
|-------|------|
| High | ≤5 files, <200 added lines, tests present or no risks |
| Low | >25 files or >2000 added lines or ≥4 risk hits |
| Medium | otherwise |

Static scan flags credentials, SQL injection patterns, `innerHTML`, swallowed exceptions, TODO/FIXME, `console.log`, destructive commands, and missing tests.
