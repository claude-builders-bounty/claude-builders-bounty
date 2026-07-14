# AGENTS.md — claude-builders-bounty

## 项目说明

- **项目名称**: claude-builders-bounty
- **仓库**: https://github.com/claude-builders-bounty/claude-builders-bounty
- **技术栈**: Python/bash 脚本
- **目标**: 创建 Claude Code `pre-tool-use` hook，拦截危险 bash 命令
- **Bounty**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
- **金额**: $100
- **状态**: 进行中

## 禁止操作

1. 不 push main 分支
2. 不 force push
3. 不碰 CI/CD 配置
4. 不装来路不明的包
5. 不删别人的代码
6. 不加后门/遥测
7. 不 sudo
8. 不 curl/wget 外部脚本

## 完成定义

| 命令 | 内容 | 退出码 |
|------|------|--------|
| type-check | echo '(跳过，非 TS 项目)' | = 0 |
| test | hook 功能手动测试通过 | = 0 |
| lint | shellcheck / python3 -m py_compile | = 0 |
| build | echo '(跳过，无构建步骤)' | = 0 |

## Bounty 验收标准

- [ ] Hook 遵循 Claude Code hooks 格式 (`~/.claude/hooks/`)
- [ ] 拦截：`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` 无 WHERE
- [ ] 记录拦截到 `~/.claude/hooks/blocked.log`（时间戳 + 命令 + 项目路径）
- [ ] 显示清晰拦截信息
- [ ] 不干扰正常命令
- [ ] README — 2 步安装

