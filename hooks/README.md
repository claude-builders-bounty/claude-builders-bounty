# bash-guardian — Claude Code 危险命令拦截 Hook

拦截以下危险 bash 命令,避免 Claude 误删数据:

| 模式 | 说明 |
|---|---|
| `rm -rf /` | 递归强制删除根目录 |
| `DROP TABLE` | 删除数据库表 |
| `TRUNCATE TABLE` | 清空数据库表 |
| `git push --force` / `-f` | 强制覆盖远端历史 |
| `DELETE FROM` (无 WHERE) | 无条件的全表删除 |
| `Format C:` | Windows 格式化 |
| `del /S /Q` `rd /S /Q` | Windows 递归强制删除 |

每次拦截都会记录到 `~/.claude/hooks/blocked.log`(时间戳 + 命令 + 项目路径),
且向 Claude 返回清晰的拦截原因,不干扰正常命令。

## 安装(2 步)

```bash
mkdir -p ~/.claude/hooks && cp bash-guardian.py ~/.claude/hooks/
echo '{"hooks":{"preToolUse":["~/.claude/hooks/bash-guardian.py"]}}' > ~/.claude/settings.json
```

## 测试

```bash
python3 - <<'EOF'
import sys, io
sys.path.insert(0, '.')
buf = io.StringIO()
sys.stdout = buf
exec(open('bash-guardian.py').read().replace("if __name__ == '__main__':\n    main()", ""))
for cmd, expect in [
    ('rm -rf /', False),
    ('rm -rf /tmp/build', True),
    ('DROP TABLE users', False),
    ('SELECT * FROM users', True),
    ('git push --force origin main', False),
    ('git push origin main', True),
    ('DELETE FROM logs', False),
    ('DELETE FROM logs WHERE id > 100', True),
    ('ls -la /tmp', True),
]:
    ok, reason = check_command(cmd)
    status = 'BLOCKED' if not ok else 'allowed'
    mark = 'PASS' if (ok == expect) else 'FAIL'
    print(f'{mark}: {status:7s} {cmd} {("| "+reason) if reason else ""}')
EOF
```