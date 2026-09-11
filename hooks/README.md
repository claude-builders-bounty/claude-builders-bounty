# Pre-tool destructive bash block hook (Claude Code)

## Install (2 commands)
```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-bash.sh
```
Then add to Claude Code settings (project or user):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/block-destructive-bash.sh" }]
      }
    ]
  }
}
```

## Behavior
- **Exit 2** → block tool; clear stderr message for Claude
- **Exit 0** → allow normal bash
- Blocks: `rm -r/-rf`, `DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE`, `git push --force`, pipe-to-shell, `dd` to devices, fork bomb
- Logs each block to `~/.claude/hooks/blocked.log` as: `timestamp project=... reason=... cmd=...`

## Test
```bash
echo '{"command":"rm -rf /"}' | bash hooks/block-destructive-bash.sh; echo $?   # 2
echo '{"command":"ls"}' | bash hooks/block-destructive-bash.sh; echo $?          # 0
```
