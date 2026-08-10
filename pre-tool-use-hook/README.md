# Claude Code 危险命令拦截 Hook

拦截 `rm -rf`、`DROP TABLE`、`TRUNCATE`、无 `WHERE` 的 `DELETE FROM`、`git push --force`、`git reset --hard` 等危险 bash 命令，记录日志并给出明确原因。正常命令完全不受影响。

## 安装（2 条命令）

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/
cp settings.snippet.json ~/.claude/settings.json   # 若已有 settings.json，请手动合并 hooks 字段
```

若你已有 `~/.claude/settings.json`，只合并其中的 `hooks.pre_tool_use` 配置即可。

## 工作原理

Claude Code 每次执行 Bash 前调用本 hook（符合官方 hooks 规范，见 `settings.snippet.json`）。脚本从 stdin 读取 `{tool_name, tool_input.command, cwd}`，命中危险模式即返回 `decision: "block"`，并把时间、命令、项目路径写入 `~/.claude/hooks/blocked.log`。

## 验证

```bash
echo '{"tool_name":"Bash","cwd":"/tmp","tool_input":{"command":"rm -rf /"}}' | python3 ~/.claude/hooks/pre_tool_use.py
```

应输出 `"decision": "block"`；普通命令（如 `ls`、`npm run build`）输出 `"decision": "approve"`。
