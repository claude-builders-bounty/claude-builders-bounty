# Bounty Fix Task

## Issue
**Title:** [BOUNTY $50] SKILL: Generate a structured CHANGELOG from git history
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
**Reward:** $50.00

## Description
## 💰 Bounty: $50 — powered by [Opire](https://opire.dev)

## Description
Create a Claude Code skill (`SKILL.md`) or a bash script that automatically generates
a structured `CHANGELOG.md` from a project's git history.

## Acceptance Criteria
- [ ] Works via `/generate-changelog` command or `bash changelog.sh`
- [ ] Fetches commits since the last git tag
- [ ] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [ ] Outputs a properly formatted `CHANGELOG.md`
- [ ] Tested on a real GitHub repo (include a sample output in the PR)
- [ ] README with setup instructions in 3 steps or fewer

## How to Claim
1. Comment `/opire try` in this issue
2. Submit a PR with your solution
3. Payment is released automatically on merge ✅

## Accepted Stack
Bash, Python, or native Claude Code `SKILL.md`.

## Instructions
1. Read the issue carefully and understand exactly what needs to be fixed.
2. Find the relevant files using grep/glob tools.
3. Implement the minimal correct fix — do not refactor unrelated code.
4. Run any existing tests to verify correctness: look for test scripts in package.json, Makefile, or similar.
5. If tests fail, fix them or update them if the behavior change is intentional.
6. Commit all changes with message: "fix: [BOUNTY $50] SKILL: Generate a structured CHANGELOG from git history"
7. Do NOT create the PR — the agent script handles that.
8. When done, write a one-paragraph summary of what you changed to AGENT_SUMMARY.md.

## Important
- Stay focused on the specific issue, nothing else.
- If the fix is unclear or requires significant architectural decisions, write your uncertainty to AGENT_SUMMARY.md and stop.
- Do not modify unrelated files.
