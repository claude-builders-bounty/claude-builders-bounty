# Claude Code Safe Bash Hook

This pre-tool-use hook intercepts destructive bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and unbounded `DELETE FROM`) before Claude can execute them. Blocked attempts are automatically logged.

## Installation

Install this hook in 2 commands:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## How it works

When Claude attempts to use a command tool, the hook intercepts the JSON payload, parses the `command` string, and checks it against a list of dangerous patterns. If a match is found:
1. It writes a log entry to `~/.claude/hooks/blocked.log` containing the timestamp, command, and current working directory.
2. It exits with code `1` and prints a clear message to Claude explaining why the command was blocked.
3. For normal commands, it exits with code `0` and allows execution to proceed normally.
