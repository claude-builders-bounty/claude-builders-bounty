# Claude Code Dangerous Command Blocking Hook

A lightweight pre-tool-use security hook for Claude Code that prevents the execution of destructive terminal and database commands before they run.

## Installation

Run these two commands in your terminal:

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py