# Block Destructive Bash Commands Hook

A safety hook for Claude Code (and other CLI agents) to prevent accidental system damage by blocking known destructive bash commands.

## Overview

This hook intercepts bash commands before they are executed. It uses a regex-based pattern matching system to identify potentially dangerous operations like recursive deletions on root, formatting disks, or overwriting critical system files.

## Files

- `pre-tool-use.sh`: The execution hook script.
- `destructive_patterns.txt`: A newline-separated list of regex patterns for blocking.

## Installation for Claude Code

To use this with Claude Code, you can configure it as a pre-tool-use hook.

1.  Copy the files to your project or a global location.
2.  Add the following to your `CLAUDE.md` or configuration:

```markdown
# Hooks
pre-tool-use: /path/to/block-destructive-commands/pre-tool-use.sh "$TOOL_COMMAND"
```

## How to Customize

Edit `destructive_patterns.txt` to add or remove patterns. Each line is treated as a regular expression.

### Example Patterns

- `rm\s+-r?[fF]?\s+/.*`: Blocks `rm -rf /` and variants.
- `mkfs\..*`: Blocks any `mkfs` command.
- `dd\s+if=.*of=/dev/.*`: Blocks writing directly to device files.

## Safety Note

While this hook provides a layer of protection, it is not exhaustive. Always review commands suggested by AI before execution.
