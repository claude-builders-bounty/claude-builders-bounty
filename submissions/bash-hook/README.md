# Pre-Tool-Use Hook

Intercepts destructive bash commands before execution.

## Install
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/

## Blocks
- Recursive force delete
- Git force push
- SQL drop / truncate / unconditional delete
- World-writable permissions
- Fork bombs and disk format operations

## Behavior
- Intercepts bash and run_shell_command tools
- Logs blocked attempts with timestamp, command, working directory
- Non-bash tools pass through untouched
