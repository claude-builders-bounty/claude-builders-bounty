#!/usr/bin/env python3
import sys
import json

def main():
    # 从系统读取 Claude 想要执行的命令
    try:
        input_data = json.load(sys.stdin)
    except:
        sys.exit(0)

    # 获取工具名称和参数
    tool_name = input_data.get('tool_name', '')
    arguments = input_data.get('arguments', {})
    command = arguments.get('command', '')

    # 危险命令黑名单
    danger_patterns = ["rm -rf", "DROP TABLE", "git push --force", "TRUNCATE"]

    # 检查是否包含危险命令
    if tool_name == "bash":
        for pattern in danger_patterns:
            if pattern in command:
                # 发现危险！告诉 Claude 停止执行并报错
                result = {
                    "decision": "block",
                    "reason": f"Security alert: The command contains a forbidden pattern: {pattern}"
                }
                print(json.dumps(result))
                return

    # 如果没问题，告诉 Claude 可以继续
    print(json.dumps({"decision": "proceed"}))

if _name_ == "_main_":
    main()
