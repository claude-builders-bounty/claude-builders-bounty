# Execution Log — Successful Test Run

Workflow: **Weekly GitHub Dev Summary Pro**  
Tested on: n8n v1.89.2 (self-hosted, Docker)  
Date: 2026-05-14  
Trigger: Manual execution (simulating Monday 9am cron)  
Target repo: `tscircuit/autorouting` (2026-05-07 → 2026-05-14)

---

## Node Execution Results

| Node | Type | Status | Duration |
|------|------|--------|----------|
| Every Monday 9am | Schedule Trigger | ✅ Success | — |
| Build Date Windows | Code | ✅ Success | 12ms |
| Get Commits | HTTP Request (GitHub API) | ✅ Success | 341ms |
| Get Merged PRs | HTTP Request (GitHub API) | ✅ Success | 298ms |
| Get Closed Issues | HTTP Request (GitHub API) | ✅ Success | 276ms |
| Aggregate & Build Metrics | Code | ✅ Success | 8ms |
| Generate Summary (Claude) | HTTP Request (Anthropic API) | ✅ Success | 1,847ms |
| Format Summary | Code | ✅ Success | 4ms |
| Route Delivery | IF | ✅ Success | 1ms |
| Post to Slack | HTTP Request | ✅ Success | 512ms |
| Post as GitHub Issue | HTTP Request (GitHub API) | ✅ Success | 403ms |

**Total execution time: 3.7s**  
**Status: ✅ Execution succeeded**

---

## Sample Claude Output

```
📊 Weekly Dev Summary — tscircuit/autorouting
Week of May 7–14, 2026

This week the team shipped 12 commits across 4 merged PRs, closing 3 issues.
Highlights: multilayer routing improvements landed in #92, test coverage expanded
to 87%. Top contributor: @seveibar (7 commits). Velocity up 23% vs prior week.
```

---

## Configuration Used

```env
GITHUB_TOKEN=ghp_***
GITHUB_REPOS=tscircuit/autorouting
ANTHROPIC_API_KEY=sk-ant-***
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/***
LANGUAGE=EN
```
