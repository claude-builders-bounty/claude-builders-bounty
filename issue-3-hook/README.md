# Claude Code Pre-tool-use Hook: Block Destructive Commands

This hook intercepts and blocks dangerous bash commands before Claude Code executes them.

## Features
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` (without a `WHERE` clause).
- Logs blocked attempts to `~/.claude/hooks/blocked.log` (includes timestamp, command, and project path).
- Provides a clear message to Claude explaining why the command was blocked.
- Does not interfere with regular, safe bash commands.

## Installation

Run the following two commands to install the hook:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use
```

## How it works
Claude Code invokes the `pre-tool-use` hook passing the tool name as the first argument, and the tool's JSON parameters via stdin. The Python script parses the `command` argument and evaluates it against a set of destructive regular expression patterns. If a match is found, the script exits with a non-zero code, preventing the tool from running, and outputs a clear rejection message to standard output which Claude can read.
