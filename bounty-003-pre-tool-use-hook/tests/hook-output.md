Sample hook output
==================

echo '{"tool":"bash","arguments":{"command":"rm -rf /tmp/test"}}' | python pre_tool_use.py

stderr:
Blocked by pre-tool-use hook: "rm -rf /tmp/test"
Reason: rm -rf / recursive force delete
This command would be destructive/irreversible. Re-consider: is there a safe, reversible alternative?

Exit code: 1

echo '{"tool":"bash","arguments":{"command":"echo ok"}}' | python pre_tool_use.py

Exit code: 0 (passthrough)

echo '{"tool":"bash","arguments":{"command":"DELETE FROM users;"}}' | python pre_tool_use.py

stderr:
Blocked by pre-tool-use hook: "DELETE FROM users;"
Reason: DELETE FROM without WHERE
This command would be destructive/irreversible. Re-consider: is there a safe, reversible alternative?

Exit code: 1
