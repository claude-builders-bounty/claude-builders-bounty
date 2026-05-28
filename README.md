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

## Claude PR Review Agent

`claude-review.js` is a zero-dependency Node.js CLI that reviews a GitHub pull request diff and emits a structured Markdown review comment. It is designed for quick local use and for automated pull request comments through GitHub Actions.

### Setup

Requirements:

- Node.js 18 or newer
- A GitHub token with access to the repository being reviewed

```bash
export GITHUB_TOKEN=ghp_your_token_here
node claude-review.js --pr https://github.com/owner/repo/pull/123
```

The token can also be passed explicitly:

```bash
node claude-review.js --token ghp_your_token_here --pr https://github.com/owner/repo/pull/123
```

### CLI Usage

```bash
node claude-review.js --pr https://github.com/owner/repo/pull/123
node claude-review.js --pr https://github.com/owner/repo/pull/123 --output review.md
node claude-review.js --diff-file ./sample.diff
```

The output includes:

- Summary of changes in 2-3 sentences
- Risks categorized as High, Medium, and Low
- Improvement suggestions
- Confidence score of Low, Medium, or High

### Risk Detection

High-risk signals:

- Authentication, authorization, password, session, OAuth, JWT, crypto, or security files
- `eval()` or `new Function()`
- `innerHTML` or `dangerouslySetInnerHTML`

Medium-risk signals:

- Database, schema, migration, or SQL files
- Configuration, CI, Docker, environment, and lock files
- Large pull requests with many files or changed lines

Low-risk signals:

- Large individual file changes
- `console.log`, `console.debug`, or `console.trace`
- `TODO` or `FIXME` markers

### GitHub Action

The workflow in `.github/workflows/claude-review.yml` runs on pull requests, generates `claude-review.md`, and posts the Markdown as a PR comment using the built-in `GITHUB_TOKEN`.

If you prefer to keep workflows in a consuming repository, copy `.github/workflows/claude-review.yml` and `claude-review.js` into that repository.

### Sample Output

```markdown
## Claude PR Review

### Summary
This review covers PR #123 titled "Add login callback", which changes 4 files with 182 additions and 31 deletions. The most common touched file types are 2 .js, 1 .yml, 1 .sql. The analysis is heuristic and should be paired with human review for domain-specific correctness.

### Identified Risks
### High
- **Authentication or security-sensitive code changed:** Review authorization boundaries, secret handling, and failure paths carefully. Files: `src/auth/callback.js`.

### Medium
- **Database or migration file changed:** Schema and data migrations need rollback, ordering, and production data compatibility checks. Files: `db/migrations/001_users.sql`.
- **Configuration or automation file changed:** Config updates can alter deployment, dependency, or CI behavior outside the touched code path. Files: `.github/workflows/deploy.yml`.

### Low
- **Debug logging present:** Console logging may leak noisy or sensitive runtime details if it ships to production. Files: `src/auth/callback.js`.

### Improvement Suggestions
- Ask for explicit security-focused review on authentication, authorization, and secret-handling changes.
- Document migration order, rollback behavior, and any expected data backfill impact.
- Remove temporary debug logging or gate it behind an appropriate logger level.

### Confidence Score
Medium
```

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
