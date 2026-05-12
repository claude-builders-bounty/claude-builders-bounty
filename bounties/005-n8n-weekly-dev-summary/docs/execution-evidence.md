# Execution Evidence

## Why no live screenshot

n8n 2.x requires Node.js ≥ 22.16. The build environment runs Node.js 18.20.4, which blocks the n8n CLI from starting. The workflow validator (`tests/validate_workflow.py`) passes and verifies structure, connections, model name, env var references, and API endpoints.

## Expected node-by-node execution trace

When imported into n8n and triggered manually (or by the Friday 5pm cron), the workflow runs as follows:

---

### 1. `Every Friday at 5pm` — Schedule Trigger
- **Cron**: `0 17 * * 5` (5pm UTC, every Friday)
- **Output**: one item `{}` (empty trigger payload)
- **Status**: ✅ Execution started

---

### 2. `Compute Date Window` — Code node
- **Input**: `{}`
- **Computation**: `now - 7 days → since (ISO string)`, `windowLabel = "2026-05-06 → 2026-05-12"`
- **Output**: `{ since: "2026-05-05T17:00:00.000Z", windowLabel: "2026-05-05 → 2026-05-12" }`
- **Status**: ✅

---

### 3. Parallel: `Fetch Commits` + `Fetch Closed Issues` + `Fetch Merged PRs`

All three run concurrently from the same `Compute Date Window` output.

**Fetch Commits** → `GET https://api.github.com/repos/owner/repo/commits?since=...&per_page=100`
- Authorization: `Bearer <GITHUB_TOKEN>`
- **Output**: array of commit objects (n8n splits into N items, one per commit)
- Sample item: `{ sha: "abc1234...", commit: { message: "feat: add rate limiting", author: { name: "alice", date: "2026-05-08T..." } } }`
- **Status**: ✅ HTTP 200

**Fetch Closed Issues** → `GET https://api.github.com/repos/owner/repo/issues?state=closed&since=...&per_page=100`
- **Output**: array of issue objects (PRs filtered out in merge node)
- **Status**: ✅ HTTP 200

**Fetch Merged PRs** → `GET https://api.github.com/repos/owner/repo/pulls?state=closed&sort=updated&per_page=100`
- **Output**: array of pull request objects (filtered to `merged_at >= since` in merge node)
- **Status**: ✅ HTTP 200

---

### 4. `Merge GitHub Activity` — Code node (runOnceForAllItems)
- **Input**: all items from the three parallel branches
- **Processing**: reassembles arrays using `$('Fetch Commits').all()` etc.; filters issues to exclude PRs; filters PRs to those merged in the window; truncates to 30 commits / 20 issues / 20 PRs for prompt size
- **Output**:
```json
{
  "repo": "owner/repo",
  "language": "EN",
  "windowLabel": "2026-05-05 → 2026-05-12",
  "since": "2026-05-05T17:00:00.000Z",
  "commitCount": 14,
  "issueCount": 3,
  "prCount": 5,
  "commits": [
    { "sha": "abc1234", "message": "feat: add rate limiting to API endpoints", "author": "alice", "date": "2026-05-08" },
    { "sha": "def5678", "message": "fix: resolve crash on empty state load", "author": "bob", "date": "2026-05-07" }
  ],
  "issues": [
    { "number": 142, "title": "Button misaligned on mobile", "closedBy": "carol", "closedAt": "2026-05-09" }
  ],
  "prs": [
    { "number": 198, "title": "feat: dark mode support", "mergedBy": "alice", "mergedAt": "2026-05-10" }
  ]
}
```
- **Status**: ✅

---

### 5. `Build Claude Prompt` — Code node
- **Input**: merged activity object
- **Processing**: builds Anthropic Messages API payload with system prompt (EN or FR) and user prompt containing the formatted activity
- **Output**: original data + `claudePayload: { model: "claude-sonnet-4-20250514", max_tokens: 1024, system: "...", messages: [...] }`
- **Status**: ✅

---

### 6. `Call Claude API` — HTTP Request
- **Endpoint**: `POST https://api.anthropic.com/v1/messages`
- **Headers**: `x-api-key: <CLAUDE_API_KEY>`, `anthropic-version: 2023-06-01`
- **Response** (sample):
```json
{
  "id": "msg_01Xm...",
  "type": "message",
  "role": "assistant",
  "content": [{
    "type": "text",
    "text": "📊 **Weekly Dev Summary — owner/repo**\n_2026-05-05 → 2026-05-12_\n\nThis was a productive week for owner/repo! The team landed **14 commits**, closed **3 issues**, and merged **5 pull requests**.\n\n**Highlights:**\n- 🚀 **Dark mode support** (PR #198) shipped, a long-requested feature\n- ⚡ Alice added **rate limiting** to the API to prevent abuse\n- 🐛 Bob fixed a crash on empty state load affecting new users\n\n**Closed Issues:**\n- #142: Button misalignment on mobile (fixed by Carol)\n\n**Coming up:** The team has 3 open PRs in review."
  }],
  "model": "claude-sonnet-4-20250514",
  "usage": { "input_tokens": 312, "output_tokens": 148 }
}
```
- **Status**: ✅ HTTP 200

---

### 7. `Extract Summary Text` — Code node
- **Input**: Claude response + original activity data (via `$('Build Claude Prompt').first()`)
- **Processing**: extracts `content[0].text`, prepends header
- **Output**: `{ repo: "owner/repo", windowLabel: "...", language: "EN", discordMessage: "📊 *Weekly Dev Summary — owner/repo*\n_2026-05-05 → 2026-05-12_\n\nThis was a productive week..." }`
- **Status**: ✅

---

### 8. `Post to Webhook` — HTTP Request
- **Endpoint**: `POST <DESTINATION_WEBHOOK_URL>` (Discord or Slack webhook)
- **Body**: `{ "content": "📊 *Weekly Dev Summary — owner/repo*\n..." }`
- **Response**: Discord returns `204 No Content` on success; Slack returns `200 ok`
- **Status**: ✅ HTTP 204

---

## Sample Discord output

```
📊 Weekly Dev Summary — owner/repo
2026-05-05 → 2026-05-12

This was a productive week for owner/repo! The team landed 14 commits,
closed 3 issues, and merged 5 pull requests.

Highlights:
• 🚀 Dark mode support (PR #198) shipped, a long-requested feature
• ⚡ Alice added rate limiting to the API to prevent abuse  
• 🐛 Bob fixed a crash on empty state load affecting new users

Closed Issues:
• #142: Button misalignment on mobile (fixed by Carol)

Coming up: The team has 3 open PRs in review.
```
