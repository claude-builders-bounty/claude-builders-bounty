# Bounty Fix Task

## Issue
**Title:** [BOUNTY $75] TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2
**Reward:** $75.00

## Description
## 💰 Bounty: $75 — powered by [Opire](https://opire.dev)

## Description
Create an opinionated, production-ready `CLAUDE.md` for a typical SaaS project
built with Next.js 15 App Router and SQLite (better-sqlite3 or Turso).

## Acceptance Criteria
- [ ] Covers: project structure, naming conventions, DB migration rules
- [ ] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [ ] Opinionated — not generic. Every rule has a reason.
- [ ] Usable without modification on a greenfield Next.js + SQLite project
- [ ] Tested: create a new project, paste the CLAUDE.md, confirm Claude Code
      understands the context without asking clarifying questions

## How to Claim
1. Comment `/opire try` in this issue
2. Submit a PR with your CLAUDE.md
3. Payment is released automatically on merge ✅

## Expected Sections
- Stack & versions
- Folder structure
- SQL / migration conventions
- Component patterns
- What we don't do (and why)

## Instructions
1. Read the issue carefully and understand exactly what needs to be fixed.
2. Find the relevant files using grep/glob tools.
3. Implement the minimal correct fix — do not refactor unrelated code.
4. Run any existing tests to verify correctness: look for test scripts in package.json, Makefile, or similar.
5. If tests fail, fix them or update them if the behavior change is intentional.
6. Commit all changes with message: "fix: [BOUNTY $75] TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project"
7. Do NOT create the PR — the agent script handles that.
8. When done, write a one-paragraph summary of what you changed to AGENT_SUMMARY.md.

## Important
- Stay focused on the specific issue, nothing else.
- If the fix is unclear or requires significant architectural decisions, write your uncertainty to AGENT_SUMMARY.md and stop.
- Do not modify unrelated files.
