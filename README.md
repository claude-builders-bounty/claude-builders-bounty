# claude-builders-bounty solutions

This repo hosts the deliverables for the claude-builders-bounty issues.

| Issue | Deliverable | File |
|-------|-------------|------|
| #1 ($50)  | Structured CHANGELOG generator | `changelog.sh` |
| #3 ($100) | Pre-tool-use destructive-command blocker | `pre_tool_use_blocker.py` |
| #4 ($150) | PR review agent (CLI) | `claude-review.py` |
| #5 ($200) | n8n weekly dev-summary workflow | `weekly-dev-summary.json` |

Each file is self-contained and documented below.

## #1 — changelog.sh (3-step setup)
```bash
# 1. Make it executable
chmod +x changelog.sh
# 2. Run inside any git repo
bash changelog.sh
# 3. (optional) since a specific tag
bash changelog.sh v1.0.0
```
Reads commits since the last tag, categorizes into Added/Fixed/Changed/Removed, writes `CHANGELOG.md`.

## #3 — pre_tool_use_blocker.py (install)
1. Save as `~/.claude/hooks/pre_tool_use_blocker.py`, `chmod +x`
2. Add to `~/.claude/settings.json`:
```json
{ "hooks": { "PreToolUse": [{ "matcher": "Bash", "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use_blocker.py" }] }] } }
```
3. Blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## #4 — claude-review.py (usage)
```bash
export GITHUB_TOKEN=your_token
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```
Emits a structured Markdown review (Summary / Risks / Suggestions / Confidence).

## #5 — weekly-dev-summary.json (n8n)
1. Import into n8n (Menu → Import from File).
2. Set variables: `GITHUB_REPO`, `GITHUB_TOKEN`, `DELIVERY_WEBHOOK`, `LANGUAGE`.
3. Activate — runs Fridays 5pm, fetches weekly GitHub activity, calls Claude, delivers via webhook.
