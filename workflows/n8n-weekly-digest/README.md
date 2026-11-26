# 每周 GitHub 动态摘要（n8n + Claude）

一条 n8n 工作流：每周五 17:00 跑一次，抓这个仓库过去 7 天的提交、已合并 PR、已关闭
issue，交给 Claude 写成一篇连贯的叙述，发到 Slack（或 Discord）。

## 五步装好

1. **导入工作流**：n8n 里 `Workflows → Import from File`，选 `weekly-github-digest.json`。
2. **加两个凭证**：
   - `HTTP Header Auth`，名字随意，Header 名 `Authorization`，值 `Bearer <你的 GitHub token>`（只读 `public_repo` 即可）。
   - 另一个 `HTTP Header Auth`，Header 名 `x-api-key`，值 `<你的 Anthropic key>`。
   两个凭证分别挂到 `GET commits / GET merged PRs / GET closed issues` 和 `Claude API` 节点上。
3. **设环境变量** `SLACK_WEBHOOK_URL`（Discord 用户换成 `DISCORD_WEBHOOK_URL`，见下文），
   并设 `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` —— n8n 默认禁止节点读环境变量，不关掉这个开关，发送节点会报 `access to env vars denied`。
4. **改 `Config` 节点**：`repo`（`owner/name`）、`channel`、`language`（`EN` 或 `FR`）、`days`（默认 7）。
5. **点 `Execute Workflow` 试跑**，看到 Slack 里出现摘要就成。

## 节点在干什么

| 节点 | 作用 |
| --- | --- |
| `Weekly (Fri 17:00)` | cron `0 17 * * 5`，每周五 17:00 |
| `Config` | 四个可调项：仓库、频道、语言、天数 |
| `Window` | 把“过去 N 天”算成 ISO 时间串 |
| `GET commits` | `GET /repos/:repo/commits?since=&until=` |
| `GET merged PRs` | 搜索 API，`is:pr is:merged merged:>=日期` |
| `GET closed issues` | 搜索 API，`is:issue is:closed closed:>=日期` |
| `Bundle` | 三路结果合成一份素材，列表截断（提交 60 条、PR 40、issue 40），防止 token 爆掉 |
| `Claude API` | `claude-sonnet-4-20250514`，`max_tokens: 1200`，system prompt 按语言切 |
| `Format` | 取 `content[].text`，为空时给可读兜底 |
| `Slack webhook` | 用 `SLACK_WEBHOOK_URL` 发出去 |

## 换 Discord

把 `Slack webhook` 节点的 URL 改成 `{{ $env.DISCORD_WEBHOOK_URL }}`，body 改成：

```json
{ "content": "**{{ $json.title }}**\n\n{{ $json.body }}" }
```

Discord 单条上限 2000 字符；摘要超过就按 1900 切段发。

## 语言

`language` 设 `FR` 时，system prompt 换成法语版本，标题也换。模型只负责叙述，
数字（提交数/PR 数/issue 数）一直是程序算的，不会因为语言而漂。

## 失败时

- GitHub 三路都开了 `retryOnFail`（3 次）。
- Claude 调用重试 2 次；返回空正文时 `Format` 会输出 `No narrative returned by the model (stop_reason: …)`，不会静默发一条空消息。
- 某一周仓库没动静也能跑：三段素材会是 `- (none)`，摘要会写“没有活动”。

## 已知边界

- GitHub 搜索 API 有速率限制（未认证 10 次/分钟，认证 30 次/分钟），一周一次足够。
- 一个仓库一次；要多仓库就复制 `Config → Slack webhook` 这一段，或改成 `Split In Batches` 遍历仓库列表。
- 摘要质量取决于提交信息质量；提交信息是 `wip`、`fix` 的仓库，读起来会很平。
