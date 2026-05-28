# Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before execution.

## Install

```bash
python3 hooks/destructive-command-blocker/install.py
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and merges the `PreToolUse` hook into `~/.claude/settings.json`.

## Blocked Patterns

- `rm -rf` variants such as `rm -fr`, `rm -Rf`, and compound shell commands containing them
- `git push --force`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSONL with:

- timestamp
- attempted command
- project path
- reason

Normal Bash commands exit silently and are not blocked.

## Sample Output

Input:

```json
{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf build"}}
```

Output:

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked recursive forced deletion pattern: rm -rf. The command was not executed. Review the command and use a safer, explicit alternative if intended."}}
```
