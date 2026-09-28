# Destructive-command pre-tool-use hook

Install: point Claude Code pre-tool-use at `.claude/hooks/pre_tool_use.py` (or `pre-tool-use.sh`).

Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE.
Writes each block to `genie-bounty-delivery/blocked.log` with a clear user message.
Normal commands (e.g. `ls`) exit 0 unaffected.
