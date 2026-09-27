# N8N Testing Results

Workflow: `workflow.json` (11 nodes). n8n instance live cần `CLAUDE_API_KEY` +
Discord webhook/email SMTP của người dùng nên phần gọi Claude + deliver chạy
khi import vào instance thật; các bước dưới verify mọi thứ còn lại.

## 1. JSON validity + importability
- `python3 -m json.tool workflow.json` parse OK (n8n import yêu cầu JSON hợp lệ).
- Nodes dùng type/version chuẩn n8n (`scheduleTrigger@1.2`, `set@3.4`,
  `httpRequest@4.2`, `code@2`, `if@2`, `emailSend@2.1`) — import thẳng không convert.

## 2. Automated tests: 10/10
`python3 tests/test_workflow_json.py`:
cron Fri 17:00, 3 GitHub fetches, model `claude-sonnet-4-20250514`,
config repo/lang/delivery, IF email-or-discord, Discord+Email deliver,
`merged_at` filter + caps (30/20/20), Claude retry x3, 7+ connections hợp lệ.

## 3. End-to-end logic trên dữ liệu thật
`python3 simulate.py opencode-ai/opencode 2025-09-01` (fetch GitHub API thật,
aggregate đúng logic Code node):
`commits=1 closed_issues=0 merged_prs=62` — xem `samples/run-log.md`
danh sách 5 PRs merged đầu + Claude prompt + Discord payload mẫu.

## 4. Chạy trên n8n thật (người dùng)
Import file → điền 4 env (`GITHUB_REPO`, `SUMMARY_LANG`, `CLAUDE_API_KEY`,
`DISCORD_WEBHOOK_URL` hoặc SMTP) → Execute 1 lần → Active để cron chạy.
