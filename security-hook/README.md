# security-hook — PreToolUse guard against destructive Bash commands

A Claude Code `pre-tool-use` hook that **blocks** dangerous Bash commands before
they run, logs every blocked attempt, and explains why — without interfering with
normal commands.

Blocks:
- `rm -rf` / recursive force deletes
- `DROP TABLE`
- `git push --force` / `--force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Install (2 commands)
```bash
cp block-destructive.py ~/.claude/hooks/
# then add to ~/.claude/settings.json:
# {"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python ~/.claude/hooks/block-destructive.py"}]}]}}
```
(An `install.py` is included that writes/merges that config for you:
`python install.py`.)

## How it works
- Reads the hook event JSON from stdin.
- Only inspects `Bash` tool calls; everything else is allowed.
- On a match: writes a line to `~/.claude/hooks/blocked.log`
  (`timestamp<TAB>command<TAB>path<TAB>reason`) and returns a `block` decision
  with a clear reason telling Claude how to proceed safely.
- On no match: returns `approve` and never touches your workflow.

## Testing
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python block-destructive.py
# -> decision: block
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python block-destructive.py
# -> decision: approve
```
