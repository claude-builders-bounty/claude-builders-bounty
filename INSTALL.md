# Install in 2 Commands

## Option 1: Bash (Linux/macOS)

```bash
cp hooks/pre-tool-use.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Option 2: Python (Cross-platform, including Windows)

```bash
cp hooks/pre_tool_use.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

Verify: Run `rm -rf /` in Claude Code — it should be blocked with a security message.
