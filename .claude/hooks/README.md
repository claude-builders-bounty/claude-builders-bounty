# PreToolUse destructive-command hook

Blocks dangerous shell commands before Claude Code executes them and records every block.

## What it blocks

| Pattern | Example |
| --- | --- |
| Recursive force delete | `rm -rf ./dist`, `rm -fr x`, `rm -r -f x`, `Remove-Item -Recurse -Force` |
| Table drop | `DROP TABLE users` |
| Forced push | `git push --force origin main`, `git push -f origin main` |
| Table truncate | `TRUNCATE TABLE orders` |
| Unscoped delete | `DELETE FROM users` (a statement with `WHERE` is allowed) |

Every blocked call writes a JSON line to `~/.claude/hooks/blocked.log` with:

- `timestamp` (UTC ISO 8601)
- `attempted_command`
- `project_path`
- `matched_pattern`

Claude receives a `permissionDecision: "deny"` with a plain explanation. Safe commands produce no output and exit 0, so normal permission flow continues.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block_destructive.py ~/.claude/hooks/block_destructive.py
cp settings.global.json ~/.claude/settings.json
```

Use `python` instead of `python3` in `settings.global.json` on Windows. For project-only scope, copy `settings.project.json` to `.claude/settings.json` and keep the script at `.claude/hooks/block_destructive.py`.

## Verification

```bash
python3 -m unittest discover -s tests -v
```

The suite covers 9 blocked commands, 6 safe commands, statement scoping, log fields, and silent pass-through.

## Design notes

- The hook is Python 3.8+ with no third-party dependencies, as required by the bounty.
- A PowerShell equivalent (`block-destructive.ps1`) is included for Windows-only setups.
- Statements are split on newlines, `;`, `&&`, and `||` before matching.
- `DELETE FROM` is allowed when the same statement contains `WHERE`.
- `CLAUDE_HOOK_LOG` overrides the log path; `CLAUDE_PROJECT_DIR` / `cwd` supply the project path.
- The hook never executes the command it inspects.
