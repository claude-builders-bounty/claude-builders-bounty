#!/usr/bin/env bash
# safety-hook.sh — Claude Code pre-tool-use hook，拦截危险 bash 命令
# 安装: cp safety-hook.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh

set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
TOOL_INPUT=$(cat)

# 从 JSON 中提取 command 字段
COMMAND=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# 空命令直接放行
[ -z "$COMMAND" ] && exit 0

# 危险模式列表（不区分大小写检查）
BLOCKED=0
REASON=""

# rm -rf / rm -fr（保护根目录和 home）
if echo "$COMMAND" | grep -qiE 'rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\s+/'; then
    BLOCKED=1
    REASON="rm -rf / — 递归删除根目录，极度危险"
fi

# DROP TABLE
if echo "$COMMAND" | grep -qiE 'DROP\s+TABLE'; then
    BLOCKED=1
    REASON="DROP TABLE — 删除数据库表，不可恢复"
fi

# git push --force
if echo "$COMMAND" | grep -qiE 'git\s+push\s+.*--force'; then
    BLOCKED=1
    REASON="git push --force — 强制推送会覆盖远程历史"
fi

# TRUNCATE
if echo "$COMMAND" | grep -qiE 'TRUNCATE\s+TABLE'; then
    BLOCKED=1
    REASON="TRUNCATE TABLE — 清空表数据，不可恢复"
fi

# DELETE FROM 无 WHERE
if echo "$COMMAND" | grep -qiE 'DELETE\s+FROM' && ! echo "$COMMAND" | grep -qiE 'WHERE'; then
    BLOCKED=1
    REASON="DELETE FROM 无 WHERE — 删除全表数据"
fi

# rm -rf 无指定路径（保护当前目录）
if echo "$COMMAND" | grep -qiE 'rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\s+\.'; then
    BLOCKED=1
    REASON="rm -rf . — 递归删除当前目录"
fi

# mkfs（格式化磁盘）
if echo "$COMMAND" | grep -qiE 'mkfs'; then
    BLOCKED=1
    REASON="mkfs — 格式化磁盘，销毁所有数据"
fi

# dd 写入磁盘
if echo "$COMMAND" | grep -qiE 'dd\s+.*of=/dev/'; then
    BLOCKED=1
    REASON="dd of=/dev/ — 直接写入磁盘设备"
fi

# :(){ :|:& };: fork bomb
if echo "$COMMAND" | grep -qE ':\(\)\{.*:\|:.*\}'; then
    BLOCKED=1
    REASON="Fork bomb — 耗尽系统进程"
fi

if [ "$BLOCKED" -eq 1 ]; then
    # 记录到日志
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] BLOCKED | $(pwd) | $COMMAND | $REASON" >> "$LOG_FILE"

    # 输出阻止消息（Claude 会看到这个）
    echo "🚫 命令被安全 Hook 阻止"
    echo "原因: $REASON"
    echo "命令: $COMMAND"
    echo "如需执行此命令，请用户手动在终端运行。"
    exit 2  # 非零退出码阻止执行
fi

# 安全命令，放行
exit 0
