# block-dangerous — Claude Code 危险命令钩子

Claude Code 的 `PreToolUse` 钩子：在 Bash 命令落地之前拦下 `rm -rf`、`DROP TABLE`、
`TRUNCATE`、不带 `WHERE` 的 `DELETE FROM`、`git push --force`，把每次拦截记进日志，
并回一句人话告诉 Claude 为什么被拦。

## 安装（两条命令）

```bash
git clone https://github.com/<you>/block-dangerous ~/.claude/hooks-src
python3 ~/.claude/hooks-src/install.py
```

装完重启 claude 会话。想先看它要改什么，加 `--dry-run`；想撤掉，`--uninstall`。

## 它拦什么

| 模式 | 例子 |
| --- | --- |
| `rm` 同时带递归和强制 | `rm -rf build/`、`rm -fr node_modules`、`rm -r -f ./dist`、`sudo rm --recursive --force /var/data` |
| `DROP TABLE` | `psql -c 'DROP TABLE users;'` |
| `TRUNCATE` | `psql -c 'TRUNCATE TABLE audit_log'` |
| `DELETE FROM` 无 `WHERE` | `psql -c 'DELETE FROM sessions'` |
| `git push --force` / `-f` | `git push --force origin main` |

**不拦**：`rm -r build`（只递归不强制）、`rm -f stale.log`（只强制不递归）、
`git push`、`git push --force-with-lease`、带 `WHERE` 的 `DELETE`、
以及 `echo`/`grep`/`git commit -m` 这类只是“念”到危险词、并不执行它们的命令。

## 拦截之后发生什么

1. 命令不会被执行。
2. `~/.claude/hooks/blocked.log` 追加一行，四列用 tab 分隔：
   时间戳 · 项目路径 · 拦截原因 · 命令原文（单行、截到 500 字）。
3. Claude 收到一条 `permissionDecision: deny` 和理由，于是知道该怎么拆小步骤。

样例（`SAMPLE_blocked.log`）：

```
2026-11-26T19:28:51+08:00	D:/work/demo	`rm -rf` 递归强制删除，路径一旦写错就救不回来。	rm -rf .git
```

## 怎么验证它真的拦得住

```bash
python3 tests/test_hook.py
```

13 条必须拦、14 条必须放行的用例，外加日志条数和格式检查。输出：

```
OK — 13 blocked, 14 allowed, log lines=13
```

## 配置形态

`install.py` 会把下面这段并进 `~/.claude/settings.json`（已有配置保留，原文件先备份）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/block_dangerous.py" }
        ]
      }
    ]
  }
}
```

## 已知边界

- 只看得到命令字符串，看不懂变量展开：`CMD="rm -rf /"; $CMD` 这类会漏。
- 判断依据是正则，不是 shell 解析器；极端写法（`r''m -rf`）可能绕过。
- 钩子自身出错时一律放行（fail-open），不会把会话卡死——这是有意的取舍，写在
  `block_dangerous.py` 的注释里。
