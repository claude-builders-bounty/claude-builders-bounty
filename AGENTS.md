# AGENTS.md — bounty-pr-reviewer

## Bounty
- **Issue**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
- **Prize**: $150
- **Task**: Create a Claude Code sub-agent that reviews a PR diff and returns structured Markdown

## 任务目标
1. 创建 CLI 工具 `claude-review`：`claude-review --pr https://github.com/owner/repo/pull/123`
2. 输出结构化 Markdown：Summary + Risks + Suggestions + Confidence Score
3. 可选：GitHub Action workflow
4. 在至少 2 个真实 GitHub PR 上测试
5. README 安装 + 使用说明

## 完成定义
- [ ] CLI 工具可用
- [ ] 结构化输出完整
- [ ] 在 2 个真实 PR 上测试通过
- [ ] README 完整
- [ ] `type-check` `test` `lint` `build` 四条命令全部通过

## 禁止操作
- 不修改 .git 目录
- 不删除现有代码
- 不向外部服务自动发送数据