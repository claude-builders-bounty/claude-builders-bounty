# Pre-tool-use Hook — Block Dangerous Bash Commands

A Claude Code pre-tool-use hook written in Python that intercepts dangerous bash commands before they execute.

## Blocks

| Pattern | Detection | Safe variant |
|---------|-----------|--------------|
| `rm -rf` | Both `-r` and `-f` flags present | `rm file.txt` |
| `DROP TABLE` | Case-insensitive regex | — |
| `git push --force` | `git push` + `--force`/`-f` | `git push origin main` |
| `TRUNCATE` | Case-insensitive with word boundary | — |
| `DELETE FROM` no `WHERE` | Checks for `WHERE` clause after `DELETE FROM` | `DELETE FROM t WHERE id=1` |

## Installation

```bash
mkdir -p .claude/hooks && cp pre_tool_use.py hooks.json .claude/hooks/
chmod +x .claude/hooks/pre_tool_use.py