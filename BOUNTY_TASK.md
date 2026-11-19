# Bounty Fix Task

## Issue
**Title:** [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
**Reward:** $100.00

## Description
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

## Instructions
1. Read the issue carefully and understand exactly what needs to be fixed.
2. Find the relevant files using grep/glob tools.
3. Implement the minimal correct fix — do not refactor unrelated code.
4. Run any existing tests to verify correctness: look for test scripts in package.json, Makefile, or similar.
5. If tests fail, fix them or update them if the behavior change is intentional.
6. Commit all changes with message: "fix: [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash comma"
7. Do NOT create the PR — the agent script handles that.
8. When done, write a one-paragraph summary of what you changed to AGENT_SUMMARY.md.

## Important
- Stay focused on the specific issue, nothing else.
- If the fix is unclear or requires significant architectural decisions, write your uncertainty to AGENT_SUMMARY.md and stop.
- Do not modify unrelated files.
