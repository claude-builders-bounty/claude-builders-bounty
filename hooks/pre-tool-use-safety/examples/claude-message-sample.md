# Sample: What Claude Sees When a Command Is Blocked

When the hook denies a Bash command, Claude Code shows this message to the model. The model then explains the situation to the user and asks for explicit confirmation before retrying.

## Example: User asked "clean up the build directory"

Claude attempted to run:

```bash
rm -rf /build
```

The hook returned:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Command blocked by pre-tool-use safety hook.\n\nReason: Recursive force delete (rm -rf)\n\nCommand: rm -rf /build\n\nThis pattern is on the destructive-commands blocklist because it can cause irreversible data loss.\nIf you are certain this is necessary:\n  1. Explain the impact to the user\n  2. Ask for explicit confirmation\n  3. Have the user run the command themselves in their terminal\n\nLogged to: /home/user/.claude/hooks/blocked.log"
  }
}
```

Claude then responds to the user:

> I tried to run `rm -rf /build` to clean the build directory, but the pre-tool-use safety hook blocked it. The `rm -rf` pattern is dangerous because it can delete files recursively without confirmation.
>
> Would you like to:
> 1. Run `rm -rf build` (without the leading `/` so it's relative to the project, not root) yourself in your terminal, or
> 2. Use `npm run clean` if your project has a clean script, or
> 3. Confirm you want me to retry with a safer approach (e.g., `rm -rf ./build`)?

This pattern surfaces destructive actions to the user instead of letting them slip through.
