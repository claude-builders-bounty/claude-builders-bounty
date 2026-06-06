# Sample Validation Output

Command:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf dist"},"cwd":"/tmp/demo"}' | python block_destructive_bash.py
```

Output:

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked destructive Bash command: rm -rf / rm -fr. Review the command and use a safer, scoped alternative."}}
```

Safe command:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git status"},"cwd":"/tmp/demo"}' | python block_destructive_bash.py
```

Output: no stdout, exit code `0`.
