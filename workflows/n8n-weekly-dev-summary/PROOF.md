# Proof of delivery — bounty #5 (issue #5)

## Workflow

- Importable n8n JSON: `weekly-dev-summary.json` (13 nodes)
- Weekly cron: Friday 5pm (`America/New_York`)
- GitHub API: commits, closed issues, merged PRs (paginated, fail-fast)
- Claude API: `claude-sonnet-4-20250514`
- Delivery: Discord, Slack, or email (configurable via `$env`)
- Languages: EN / FR
- Screenshot: `assets/n8n-execution-screenshot.png`

## Test evidence

Hands-on takeover (2026-06-18, PR #2541): verified repo-scoped `GITHUB_TOKEN` validation (`GET /repos/{owner}/{repo}`), full `npm test`, isolated `npm run test:peer-review` / `npm run test:delivery`, and fleet delivery gates (`no_committed_diff`, `peer_review_not_passed`) for issue #5.

Prior verification (2026-06-17): same suite plus `npm run test:github`.

From repository root:

```bash
npm test
```

Expected CI runner output (suite counts may grow; total must stay in sync):

```
OK: 13 nodes, all acceptance checks passed.
OK: GitHub data collection handles n8n item splitting.
OK: github-collect unit tests passed.
OK: workflow integration tests passed.
OK: 10 test scripts validated.
Ran 18 delivery verification tests — OK
Ran 43 tests — OK
OK: peer review acceptance tests passed
OK: 210 tests passed
OK: all CI validation checks passed
```

Optional live GitHub check:

```bash
npm run test:github
```

## Acceptance mapping

| Criterion | Evidence |
|-----------|----------|
| Exportable `.json` workflow | `weekly-dev-summary.json` + `validate-workflow.mjs` |
| Weekly cron (Friday 5pm) | Schedule trigger assertions in validator + peer-review suite |
| GitHub activity fetch | Fetch nodes + `github-fetch.test.mjs` |
| Claude Sonnet 4 summary | Claude API node + peer-review acceptance |
| Discord/Slack/email delivery | Route Delivery switch + README + emailTo wiring regression |
| Configurable repo/channel/language | Load Config env vars + FR localization tests |
| Real n8n test + screenshot | `assets/n8n-execution-screenshot.png` |
| README ≤ 5 setup steps | README + validator step-count check |
