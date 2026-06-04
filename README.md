# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## 🛠️ Included Tools

This repository contains two production-ready developer tools built for Claude Code:

1. **CHANGELOG Generator Skill (`generate_changelog.py`)**: Automatically parses your project's git history since the last release tag, categorizes commits into standard bins (`Added`, `Fixed`, `Changed`, `Removed`), and outputs a clean `CHANGELOG.md`.
2. **Claude PR Reviewer CLI (`claude_review.py`)**: Fetches raw PR diffs from GitHub without needing API authentication, runs static code analysis (or calls Gemini AI if configured), and writes a structured Markdown review report.

---

## 🚀 Quick Start (3 Steps or Fewer)

### 1. Slicing Git History (CHANGELOG)
Generate your changelog instantly in the current repository:
```bash
python generate_changelog.py
```

### 2. Run PR Reviews Natively
Review any public pull request via URL (it will generate `pr_review_report.md`):
* **Windows**:
  ```cmd
  claude-review --pr https://github.com/owner/repo/pull/123
  ```
* **Linux/macOS**:
  ```bash
  ./claude-review --pr https://github.com/owner/repo/pull/123
  ```

### 3. Optional: Configure Gemini AI for Reviews
Create a `.env` file in the root directory and add your API key for generative reviews:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
