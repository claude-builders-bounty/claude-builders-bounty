# Block destructive Bash commands

This submission implements a Claude Code `PreToolUse` hook that blocks dangerous
Bash commands before they run.

It denies:

- `rm` commands that combine recursive and force flags, such as `rm -rf`.
- `git push --force`, `git push -f`, `git push --force-with-lease`, and force
  refspec pushes.
- SQL containing `DROP TABLE`, `TRUNCATE`, or `DELETE FROM` without a `WHERE`
  clause.

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSONL with
the timestamp, attempted command, project path, and block reason.

## Install

From this repository root:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git && cd claude-builders-bounty
python3 .claude/hooks/block_destructive_bash.py --install
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and
adds a `PreToolUse` hook for the `Bash` tool in `~/.claude/settings.json`.

## Example block response

When Claude Code attempts a destructive command, the hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: rm with both recursive and force flags. The attempt was logged to ~/.claude/hooks/blocked.log."
  }
}
```

Safe commands such as `npm test`, `git status`, and `rm build.log` produce no
output and continue through Claude Code's normal permission flow.
