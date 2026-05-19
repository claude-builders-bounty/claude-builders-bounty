# 🛡️ Bash Guard Hook

Pre-tool-use hook for Claude Code — intercepts and blocks destructive bash commands before execution.

## ⚡ Quick Start (3 steps)

```bash
# 1. Install
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/
# OR for bash version:
cp pre_tool_use.sh ~/.claude/hooks/

# 2. Make executable
chmod +x ~/.claude/hooks/pre_tool_use.py
# OR:
chmod +x ~/.claude/hooks/pre_tool_use.sh

# 3. Claude Code auto-detects hooks — nothing else needed
```

## 🛡️ What It Blocks

| Category | Patterns Blocked | Severity |
|----------|-----------------|----------|
| File System | `rm -rf /`, `dd`, `mkfs`, `> /dev/sd*`, `chmod 777 /` | 🔴 Critical |
| Database | `DROP TABLE`, `DROP DATABASE`, `DELETE FROM` without WHERE | 🔴 Critical |
| Git | `push --force`, `reset --hard`, force-delete remote branches | 🟠 High |
| System | `curl \| bash`, `wget \| bash`, overwrite `.bashrc`, `shutdown` | 🟠 High |
| Docker | `docker prune`, `compose down -v`, volume rm | 🟡 Medium |

## ✅ Smart Whitelist

Common safe operations are explicitly allowed:
- `rm -rf node_modules .next dist build __pycache__`
- `git push --force-with-lease`
- `git clean -fd node_modules`

## 📂 Files

| File | Description |
|------|-------------|
| `pre_tool_use.py` | Python version (richer pattern matching) |
| `pre_tool_use.sh` | Pure bash version (zero dependencies) |

## 🧪 Test It

```bash
# Should BLOCK:
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"}}' | python3 pre_tool_use.py
echo '{"tool_name":"bash","tool_input":{"command":"DROP TABLE users;"}}' | python3 pre_tool_use.py

# Should ALLOW:
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"}}' | python3 pre_tool_use.py
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf node_modules"}}' | python3 pre_tool_use.py
```
