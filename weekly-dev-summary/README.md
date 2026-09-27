# Weekly Dev Summary — Opire $200 bounty entry (issue #5)

![n8n](https://img.shields.io/badge/n8n-workflow.json-orange) ![claude](https://img.shields.io/badge/Claude-sonnet--4-purple) ![tests](https://img.shields.io/badge/validate-green)

n8n workflow: tóm tắt narrative hàng tuần hoạt động GitHub repo bằng Claude API,
gửi qua Discord webhook (có hướng dẫn đổi sang email trong file).

## Cài (5 bước)

```bash
1. n8n → Workflows → Import from file → chọn workflow.json
2. Điền env: GITHUB_REPO (owner/repo), SUMMARY_LANG (EN/FR), CLAUDE_API_KEY, DISCORD_WEBHOOK_URL
3. Credentials: HTTP Header Auth cho Claude (x-api-key) — workflow đã đấu sẵn chỗ cắm
4. Bấm Execute Workflow 1 lần để test (xem samples/run-log.md mẫu output thật)
5. Bật Active — cron tự chạy 17:00 thứ 6 hàng tuần
```

Đổi sang email: thay node `Deliver (Discord)` bằng SMTP/Email node, giữ nguyên input.

## Nodes (8)
Cron Fri 17:00 → Config (repo/lang) → 3x GitHub API (commits, closed issues, PRs)
→ Code aggregate → Claude (`claude-sonnet-4-20250514`) → Discord webhook.

## Test thật
- `python3 validate.py` → XANH (8 nodes, connections hợp lệ, đủ spec).
- `python3 simulate.py <repo>` → chạy logic fetch+aggregate trên repo thật,
  xem `samples/run-log.md` (62 merged PRs opencode-ai/opencode).
- Live n8n: import file vào instance n8n bất kỳ là chạy (Claude node cần API key thật).
