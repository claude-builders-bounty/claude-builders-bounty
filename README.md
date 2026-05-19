# Dangerous Command Blocker

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
curl -sL https://raw.githubusercontent.com/niufox/claude-builders-bounty/main/pre-tool-use.py \
  -o ~/.claude/hooks/pre-tool-use/dangerous-command-blocker.py && chmod +x "$_"
```

## Blocked Patterns

### File System Destruction
| Pattern | Description |
|---------|-------------|
| `rm -rf /` | System root deletion |
| `rm -rf /*` | Wildcard root deletion |
| `sudo rm -rf /` | Privileged system deletion |
| `dd if=/dev/zero` | Disk overwrite |
| `dd if=/dev/urandom` | Random disk overwrite |
| `mkfs` / `mkfs.ext4` | Filesystem creation (destructive) |
| `format C:` | Drive formatting |

### Database Destruction
| Pattern | Description |
|---------|-------------|
| `DROP TABLE` | Table deletion |
| `DROP DATABASE` | Database deletion |
| `TRUNCATE` | Table truncation |
| `DELETE FROM` (no WHERE) | Mass deletion |

### Git Force Push
| Pattern | Description |
|---------|-------------|
| `git push --force` | Force push |
| `git push -f` | Force push (short form) |

### System Operations
| Pattern | Description |
|---------|-------------|
| `chmod -R 777` | Dangerous recursive permissions |
| `chown -R` | Recursive ownership change |
| `shutdown` / `reboot` / `poweroff` | System shutdown |
| `mv /` | Moving root directory |
| `:(){ :\|:& };:` | Fork bomb |

### Remote Code Execution
| Pattern | Description |
|---------|-------------|
| `curl ... \| bash` | Piped internet script |
| `wget ... \| bash` | Piped internet script |
| `eval "$(curl ...)"` | Eval remote content |
| `bash <(curl ...)` | Subprocess from network |

### System Config & Packages
| Pattern | Description |
|---------|-------------|
| `> /etc/` | System config modification |
| `sudo tee /etc/` | Privileged config write |
| `apt-get remove --purge` | Destructive package removal |
| `docker system prune -a` | Destroy all containers/images |

## Safe Allowlist

The hook automatically allows `rm -rf` on common build directories:

```
node_modules, .next, dist, build, target, __pycache__,
.venv, venv, .git, .terraform, coverage, .turbo, tmp
```

## User Allowlist

To allow a specific command, add it to `~/.claude/hooks/allowed-dangerous.json`:

```json
{"allowed_commands": ["rm -rf /tmp/experimental"]}
```

## How It Works

- Runs before every tool call in Claude Code
- Only intercepts Bash/terminal commands
- Blocks dangerous patterns and logs details to `~/.claude/hooks/blocked.log`
- Safe commands (including build cleanup) pass through without interference
- Fully compatible with multi-line and chained commands (`&&`, `||`, `;`)

## Log File

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-19 14:30:00] Blocked: rm -rf (recursive force delete)
  Command: rm -rf /important/data
  Project: /Users/me/my-project
  CWD:     /Users/me/my-project
  ---
```

## Requirements

- Python 3.6+
- Claude Code CLI

## License

MIT
