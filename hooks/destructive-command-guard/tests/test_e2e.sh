#!/bin/bash
export BLOCKED_LOG_PATH="/tmp/claude_test_blocked.log"
rm -f "$BLOCKED_LOG_PATH"

echo "Running SAFE test..."
OUT1=$(echo '{"tool_name":"Bash","tool_input":{"command":"echo hello"},"cwd":"/tmp"}' | ./hooks/destructive-command-guard/pre-tool-use 2>&1)
EXIT1=$?
if [ $EXIT1 -ne 0 ]; then
    echo "SAFE test failed with exit code $EXIT1"
    exit 1
fi

echo "Running BLOCK test..."
OUT2=$(echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp"}' | ./hooks/destructive-command-guard/pre-tool-use 2>&1)
EXIT2=$?
if [ $EXIT2 -eq 0 ]; then
    echo "BLOCK test failed: did not exit nonzero"
    exit 1
fi
if ! grep -q "Command Execution Blocked by Policy" <<< "$OUT2"; then
    echo "BLOCK test failed: did not output correct stderr message"
    exit 1
fi
if [ ! -f "$BLOCKED_LOG_PATH" ]; then
    echo "BLOCK test failed: did not write log file"
    exit 1
fi

echo "✅ All E2E hook tests passed! INTEGRATION_VERIFIED"
