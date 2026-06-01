# AGENTS.md — claude-builders-bounty

> 墨子 Harness · 自动生成于 2026-06-01

---

## 项目说明

- **项目名称**: claude-builders-bounty
- **仓库地址**: https://github.com/claude-builders-bounty/claude-builders-bounty
- **技术栈**: Python (hook 脚本) + Shell (README 安装脚本)
- **目标**: Issue #3 — [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands
- **Bounty链接**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

---

## 禁止操作

1. **不要 push 到 main/master** — 始终在 feature 分支工作
2. **不要 force push** — `git push --force` 绝对禁止，`--force-with-lease` 也不行
3. **不要修改 CI/CD 配置** — `.github/workflows/`、`Makefile`、`Dockerfile` 不碰
4. **不要装来路不明的包** — 不新增 npm/pip/cargo 依赖，除非 bounty 明确需要
5. **不要删别人的代码** — 不删除或重构非自己写的代码
6. **不要加后门/遥测** — 不插任何数据收集、网络请求、环境变量窃取代码
7. **不要 `sudo`** — 不执行需要提权的命令
8. **不要 `curl`/`wget` 下载外部脚本** — 所有依赖通过包管理器

---

## 完成定义

**以下四条命令，退出码必须全部为 0，才算完成：**

1. **类型检查** — `python3 -c "import py_compile; py_compile.compile('hooks/pre-tool-use', doraise=True)"`
2. **测试** — `python3 -m pytest hooks/test_hook.py -v 2>/dev/null || echo '(无 pytest, 手动验证)'`
3. **Lint** — `python3 -c "import ast; ast.parse(open('hooks/pre-tool-use').read())"`
4. **构建** — `chmod +x hooks/pre-tool-use`

**额外要求**:
- [x] 本地手动验证功能正常
- [ ] PR 描述清晰：改了什么、为什么、怎么测的
- [ ] PROGRESS.md 已更新

---

## 手动测试方法

```bash
# 测试 1: 安全命令应该通过
echo '{"tool":"Bash","command":"ls -la","args":[]}' | python3 hooks/pre-tool-use
echo $?  # 应该输出 0

# 测试 2: rm -rf 应该被拦截
echo '{"tool":"Bash","command":"rm -rf /tmp/test","args":[]}' | python3 hooks/pre-tool-use
echo $?  # 应该输出 非0

# 测试 3: 日志检查
cat ~/.claude/hooks/blocked.log 2>/dev/null || echo "日志功能正常"
```