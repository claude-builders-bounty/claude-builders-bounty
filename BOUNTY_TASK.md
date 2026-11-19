# Bounty Fix Task

## Issue
**Title:** [BOUNTY $150] AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
**Reward:** $150.00

## Description
## 💰 Bounty: $150 — powered by [Opire](https://opire.dev)

## Description
Create a Claude Code agent that takes a PR diff as input, analyzes it,
and returns a structured Markdown review comment.

## Acceptance Criteria
- [ ] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [ ] OR via GitHub Action (include the workflow YAML)
- [ ] Structured Markdown output with:
  - Summary of changes (2–3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High
- [ ] Tested on at least 2 real GitHub PRs (include outputs in the PR)
- [ ] README with setup and usage instructions

## How to Claim
1. Comment `/opire try` in this issue
2. Submit a PR with the agent + sample outputs
3. Payment is released automatically on merge ✅

## Instructions
1. Read the issue carefully and understand exactly what needs to be fixed.
2. Find the relevant files using grep/glob tools.
3. Implement the minimal correct fix — do not refactor unrelated code.
4. Run any existing tests to verify correctness: look for test scripts in package.json, Makefile, or similar.
5. If tests fail, fix them or update them if the behavior change is intentional.
6. Commit all changes with message: "fix: [BOUNTY $150] AGENT: Claude Code sub-agent that reviews a PR and posts a"
7. Do NOT create the PR — the agent script handles that.
8. When done, write a one-paragraph summary of what you changed to AGENT_SUMMARY.md.

## Important
- Stay focused on the specific issue, nothing else.
- If the fix is unclear or requires significant architectural decisions, write your uncertainty to AGENT_SUMMARY.md and stop.
- Do not modify unrelated files.
