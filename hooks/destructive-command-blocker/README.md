# 🛡️ Destructive Command Blocker (Claude Code Hook)

A robust, context-aware `pre-tool-use` hook for Claude Code that prevents accidental execution of dangerous commands.

## Features
- **Comprehensive Protection**: Shields your environment from dangerous File System, SQL, Git, and DevOps commands.
- **Smart SQL Detection**: Distinguishes between safe `DELETE` statements (with `WHERE`) and destructive ones (without `WHERE`).
- **Safe Alternatives**: Provides actionable suggestions (e.g., using `--force-with-lease` instead of `--force`).
- **Audit Logging**: Logs all blocked attempts to `~/.claude/hooks/blocked.log` for review.
- **Customizable**: Add your own patterns or whitelist commands via `~/.claude/hooks/blocker_config.json`.
- **Zero Dependencies**: Written in pure Python 3.

## Covered Patterns
| Category | Examples |
| :--- | :--- |
| **File System** | `rm -rf /`, `rm -rf *`, `chmod -R 777 /` |
| **Databases** | `DROP TABLE`, `TRUNCATE`, `DELETE`/`UPDATE` without `WHERE` |
| **Git** | `git push --force`, `git branch -D` |
| **DevOps** | `docker rm -f $(...)`, `kubectl delete --all` |

## Quick Install (2 Commands)

```bash
mkdir -p ~/.claude/hooks
curl -sSL https://raw.githubusercontent.com/Mohamed-elgypaly/claude-builders-bounty/feat/destructive-command-blocker/hooks/destructive-command-blocker/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

*Note: Replace `Mohamed-elgypaly` with the upstream repo owner if merged, or your own fork for testing.*

## Configuration
You can optionally create `~/.claude/hooks/blocker_config.json` to customize behavior:

```json
{
  "whitelist": ["git push --force-with-lease"],
  "custom_patterns": [
    {
      "regex": "my-dangerous-command",
      "message": "This command is restricted in our team.",
      "suggestion": "Contact @admin for approval."
    }
  ]
}
```
