# n8n verification — local instance state

- Database file: `C:\Users\Administrator\.openclaw\workspace\bounties\.n8n-data\.n8n\database.sqlite`
- Workflows imported: **1**

## Workflow: `weekly-dev-summary` — Weekly Dev Summary (Claude)

- Active: `False`
- Node count: **11**

### Nodes (in graph layout order)

| Position | Type | Name | Notes |
|---|---|---|---|
|  240,  300 | `n8n-nodes-base.scheduleTrigger` | Friday 5 PM Cron | Fires at 17:00 in the n8n instance's local time zone every F… |
|  460,  300 | `n8n-nodes-base.set` | Config (env) | All knobs come from env. GITHUB_REPO defaults to pallets/cli… |
|  720,  180 | `n8n-nodes-base.httpRequest` | GitHub: commits last 7d |  |
|  720,  320 | `n8n-nodes-base.httpRequest` | GitHub: closed issues last 7d |  |
|  720,  460 | `n8n-nodes-base.httpRequest` | GitHub: recent PRs (filter merged) |  |
|  960,  320 | `n8n-nodes-base.code` | Aggregate week |  |
| 1220,  320 | `n8n-nodes-base.httpRequest` | Claude: narrative summary | Uses prompt caching on the system prompt — repeated runs are… |
| 1480,  320 | `n8n-nodes-base.code` | Format payload |  |
| 1720,  320 | `n8n-nodes-base.switch` | Route by destination |  |
| 1980,  220 | `n8n-nodes-base.httpRequest` | Post to Discord |  |
| 1980,  420 | `n8n-nodes-base.httpRequest` | Post to Slack |  |

### Connections (graph edges)

- `Friday 5 PM Cron` → `Config (env)` (port 0)
- `Config (env)` → `GitHub: commits last 7d` (port 0)
- `Config (env)` → `GitHub: closed issues last 7d` (port 0)
- `Config (env)` → `GitHub: recent PRs (filter merged)` (port 0)
- `GitHub: commits last 7d` → `Aggregate week` (port 0)
- `GitHub: closed issues last 7d` → `Aggregate week` (port 0)
- `GitHub: recent PRs (filter merged)` → `Aggregate week` (port 0)
- `Aggregate week` → `Claude: narrative summary` (port 0)
- `Claude: narrative summary` → `Format payload` (port 0)
- `Format payload` → `Route by destination` (port 0)
- `Route by destination` → `Post to Discord` (port 0)
- `Route by destination` → `Post to Slack` (port 0)
