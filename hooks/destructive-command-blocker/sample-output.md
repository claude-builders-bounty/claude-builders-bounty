# Sample Test Output

Tested with Python 3 on `claude-builders-bounty`.

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf build"}}' \
  | python3 hooks/destructive-command-blocker/block_destructive_bash.py
```

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked recursive forced deletion pattern: rm -rf. The command was not executed. Review the command and use a safer, explicit alternative if intended."}}
```

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"npm test"}}' \
  | python3 hooks/destructive-command-blocker/block_destructive_bash.py
```

No output; command is allowed.
