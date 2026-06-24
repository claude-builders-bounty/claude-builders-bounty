# PROGRESS.md — claude-builders-bounty

> 墨子 Harness · 自动生成于 2026-06-24

**Bounty**: $100 — Pre-tool-use hook 拦截危险 bash 命令
**Issue**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

---

## ✅ 已完成

- [x] 任务申领（`/opire try` 评论）
- [x] Harness 初始化（AGENTS.md / PROGRESS.md / setup.sh）
- [x] hook.py — 核心拦截脚本（21 条危险模式规则）
- [x] 支持拦截：rm -rf、DROP TABLE、TRUNCATE、DELETE 无 WHERE、git push --force、git reset --hard、eval、sudo rm、chmod 777、curl | bash、wget | sh、写入系统路径 等
- [x] 三级严重等级：CRITICAL / HIGH / MEDIUM
- [x] blocked.log 日志记录（时间戳 + 命令 + 项目路径）
- [x] test_hook.py — 28 个测试用例（覆盖危险拦截 + 安全放行 + 日志 + 规则完整性 + 防误报）
- [x] README.md — 安装说明（2 步）、拦截类别、日志格式、卸载说明
- [x] 四条完成命令全绿通过

## 🔄 进行中

- PR 提交流程

## 📋 待办

- 无

## ⚠️ 已知问题

- 无
