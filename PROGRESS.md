# PROGRESS.md — claude-builders-bounty

> Bounty #3: HOOK — Block destructive bash commands in Claude Code

---

## 进行中

- [x] Harness 初始化
- [x] 编写 `hooks/pre-tool-use` 脚本
- [x] 本地测试：7 种拦截模式全部通过
- [x] 更新 README 安装说明
- [ ] 提交 PR

## 已完成

- [x] 编写 hook 脚本（Python）
  - 拦截: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
  - 日志: `~/.claude/hooks/blocked.log`
  - 支持两种 Payload 格式: `{"command":"..."}` 和 `{"tool":"Bash","args":{"command":"..."}}`
- [x] 测试结果（全部通过）
  - `ls -la` → exit 0 ✅
  - `rm -rf /tmp/test` → exit 1 + message + log ✅
  - `DROP TABLE users;` → exit 1 ✅
  - `git push --force origin main` → exit 1 ✅
  - `TRUNCATE orders;` → exit 1 ✅
  - `DELETE FROM users` → exit 1 ✅
  - `DELETE FROM users WHERE id = 5` → exit 0 ✅

## 待办

- 检查四条命令（type-check / test / lint / build）

## 已知问题

- 无 Package.json（纯脚本项目），测试命令用 `python3 hooks/pre-tool-use` 手动验证