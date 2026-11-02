# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

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

---

## Claude Code PR Review Agent (Bounty #4)

An automated code review sub-agent that takes a pull request diff as input, evaluates architectural and security risks, and generates a structured Markdown review comment.

### Features
- **Dual Execution**: Run via standalone CLI (`claude-review --pr <url>`) or automated GitHub Action workflow (`.github/workflows/claude-review.yml`).
- **Structured Heuristics**:
  - 📋 **Summary of Changes**: Scope, additions/deletions, primary modules modified.
  - ⚠️ **Identified Risks**: Secrets/credentials, test coverage gaps, SQL migrations, dependency updates, and blast radius.
  - 💡 **Improvement Suggestions**: Edge cases, error handling, documentation, and interface validation.
  - 🎯 **Confidence Score**: High / Medium / Low with explicit factor reasoning.
- **Zero Heavy Dependencies**: Pure Python 3 standard library (`urllib`, `re`, `json`, `argparse`).
- **Automated Posting**: Optional `--post` flag to publish reviews directly to GitHub PR discussion threads.

### Setup & Usage

#### 1. CLI Usage
```bash
# Make executable
chmod +x claude-review

# Review any public pull request
./claude-review --pr https://github.com/owner/repo/pull/123

# Save output to Markdown file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Review and post comment back to GitHub (requires GITHUB_TOKEN or gh auth)
./claude-review --pr https://github.com/owner/repo/pull/123 --post
```

#### 2. GitHub Actions Setup
Add `.github/workflows/claude-review.yml` to your repository. It automatically triggers on pull requests and posts structured reviews back to the discussion thread.

#### 3. Run Unit Tests
```bash
python3 -m unittest discover -s tests -v
```

#### 4. Verified Sample Outputs
- [Sample Review 1 (PR #5115)](examples/SAMPLE_REVIEW_1.md)
- [Sample Review 2 (PR #5114)](examples/SAMPLE_REVIEW_2.md)

