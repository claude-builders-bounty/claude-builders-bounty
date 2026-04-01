# Bounty Fix Analysis

## Issue
- **URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
- **Title:** [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands
- **Bounty:** $100
- **Labels:** bounty, hook, security

## Tech Stack


## Issue Body
## 💰 Bounty: $100 — powered by [Opire](https://opire.dev)

## Description
Create a Claude Code `pre-tool-use` hook in Python or bash that intercepts
dangerous bash commands before they are executed.

## Acceptance Criteria
- [ ] Hook follows Claude Code hooks format (`~/.claude/hooks/`)
- [ ] Blocks these patterns: `rm -rf`, `DROP TABLE`, `git push --force`,
      `TRUNCATE`, `DELETE FROM` without a WHERE clause
- [ ] Logs every blocked attempt to `~/.claude/hooks/blocked.log`
      with: timestamp, attempted command, project path
- [ ] Displays a clear message to Claude explaining why the command was blocked
- [ ] Does not interfere with normal bash commands
- [ ] README with installation in 2 commands or fewer

## How to Claim
1. Comment `/opire try` in this issue
2. Submit a PR with the hook + README
3. Payment is released automatically on merge ✅

## Resources
- Claude Code hooks docs: https://docs.anthropic.com/claude-code/hooks

## Analysis
[AI Agent should analyze the issue and implement the fix here]

## Testing Notes
- [ ] Understand the issue requirements
- [ ] Implement the fix
- [ ] Run existing tests
- [ ] Add tests if needed
- [ ] Verify fix addresses the issue
