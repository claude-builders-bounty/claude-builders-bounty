# PR: Bounty #5 — Weekly GitHub Dev Summary (n8n + Claude)

## 对应赏金
- Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5
- 金额：$200（Opire，合并后 USDT 支付）

## 交付内容
- `bounty-5-weekly-dev-summary/Weekly-GitHub-Dev-Summary.workflow.json` — 可直接 Import 的 n8n 工作流
- `bounty-5-weekly-dev-summary/README.md` — 配置与验收说明

## 验收对照
- ✅ 可导出 n8n 工作流（`.json`）
- ✅ 每周 cron 触发（周五 17:00，`dayOfWeek:[5]`）
- ✅ 通过 GitHub REST API 拉取本周 commits / 已关闭 issues / 已合并 PRs
- ✅ 调用 `claude-sonnet-4-20250514` 生成叙述性周报
- ✅ 通过 Slack/Discord webhook 投递（兼容两种格式）
- ✅ 仓库 / 渠道 / 语言（EN/FR）均通过环境变量配置，工作流无硬编码密钥

## 实现要点
- 三路取数使用 HTTP Request 直连 GitHub REST（commits / issues / search issues `is:pr is:merged merged:>date`），避免依赖 GitHub 节点易变的资源枚举。
- `Build Prompt` 节点过滤 issues 接口混入的 PR，并按 `LANG` 切换中/英/法语指令。
- 所有密钥经 `{{ $env.* }}` 引用，导入即用。

## 测试建议
导入后在 n8n 配置 6 个环境变量（见 README），先 **Execute Workflow** 手动验证一次，再开启 Active。
