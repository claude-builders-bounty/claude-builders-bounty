# block-destructive.py

Claude Code `PreToolUse` hook that intercepts destructive bash commands **before** they execute.

## What it blocks

### Filesystem
- `rm -rf /`, `rm -rf ~`, `rm -rf .`
- `rmdir /`
- `> /dev/sdX`, `mkfs.*`, `dd of=/dev/...`
- `fork bomb :(){ :|:& };:`

### Git
- `git push --force` / `git push -f` / `--force-with-lease`
- `git reset --hard`
- `git clean -fdx`
- `git branch -D`
- `git stash drop`
- `git checkout -- .`
- `git restore --staged --worktree .`

### Database
- `DROP TABLE|DATABASE|INDEX|SCHEMA|VIEW|TRIGGER|PROCEDURE|FUNCTION|USER|ROLE`
- `TRUNCATE TABLE`
- `DELETE FROM x` without `WHERE`
- `UPDATE x SET ...` without `WHERE`
- `REVOKE ALL`

### System / privilege
- `chmod 777` / `chmod -R 777`
- `chown -R user:group /`
- `shutdown` / `reboot` / `poweroff` / `halt`
- `mkfs` / `fdisk` / `parted`
- `sudo rm -rf /`
- `diskutil eraseDisk|partitionDisk|unmountDisk` (macOS)
- `defaults delete ... ...` (macOS)

### Network exfiltration
- `curl ... | sh` / `wget ... | sh`
- `nc -e`

## Install (2 commands)

```bash
# 1. Download + make executable
curl -o ~/.claude/hooks/block-destructive.py https://raw.githubusercontent.com/phoenix7956/claude-review-bounty/main/.claude/hooks/block-destructive.py
chmod +x ~/.claude/hooks/block-destructive.py

# 2. Add to Claude Code settings (~/.claude/settings.json)
```

### `~/.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

## How it works

1. Claude Code calls the hook before every `Bash` tool use
2. Hook receives JSON on stdin: `{ "tool_name": "Bash", "tool_input": { "command": "..." }, "cwd": "..." }`
3. Hook regex-matches against the destructive pattern list
4. **Allowed**: exits 0 — Claude proceeds
5. **Blocked**: exits 2 + writes reason to stderr (Claude sees the message and explains to user) + appends a line to `~/.claude/hooks/blocked.log` with UTC timestamp, reason, command (truncated 500 chars), and cwd

## Test

```bash
# Should allow
echo "rm -rf /tmp/foo" | python3 ~/.claude/hooks/block-destructive.py
echo $?  # 0 (allowed; /tmp/foo is not a protected path)

# Should block
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/"}' | python3 ~/.claude/hooks/block-destructive.py
echo $?  # 2
# stderr: "BLOCKED by block-destructive.py: rm -rf / (root filesystem) ..."

# Check the log
cat ~/.claude/hooks/blocked.log
```

## Customize

Edit the `DESTRUCTIVE_PATTERNS` list at the top of the script. Each entry is `(regex, flags, human_reason)`. Add your own patterns or remove ones you find too aggressive. Order matters — more specific patterns should come first.

## Why this exists

Hermes (the author) lost work to a `git reset --hard` in 2024. This hook is the belt-and-suspenders companion to careful prompting.

---

Built by [@phoenix7956](https://github.com/phoenix7956) for [Bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) ($100).
