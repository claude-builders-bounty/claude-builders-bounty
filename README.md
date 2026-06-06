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

# claude-review

A Claude Code sub-agent that takes a GitHub Pull Request as input, analyses the diff with Claude, and posts a structured Markdown review comment.

Built for the `[BOUNTY $150] AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment` task in [#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

## Features

- 🤖 **Claude-powered review** — uses `claude-opus-4-7` with a strict JSON schema
- 🧱 **Pure stdlib Python** — zero third-party dependencies (Python 3.10+)
- 🔁 **Two interfaces** — CLI (`claude-review --pr ...`) and GitHub Action (`action.yml`)
- 📊 **Structured output** — Summary / Risks / Suggestions / Confidence
- 📌 **Sticky PR comment** — uses `marocchino/sticky-pull-request-comment` so the same comment is updated on every push
- 🛑 **Optional confidence gate** — fail the action if confidence is below Low/Medium/High

## CLI usage

```bash
# Review a public PR
python -m claude_review --pr https://github.com/owner/repo/pull/123

# Review a local diff file
python -m claude_review --diff path/to/changes.diff

# Emit JSON instead of Markdown
python -m claude_review --pr https://github.com/owner/repo/pull/123 --json
```

## Required environment

- `ANTHROPIC_API_KEY` — your Claude API key (always required)
- `GITHUB_TOKEN` — only for private repos or to lift the 60 req/hr unauthenticated GitHub rate limit

## GitHub Action usage

See `examples/workflow.yml` for a complete, copy-paste workflow. The action is composite and uses the agent code from this repo.

## Sample outputs

- `examples/PR-strict-kwargs-201.md` — review of a small Rust fix
- `examples/PR-anyformat-workshop-39.md` — review of a small Python fix

Both are real PRs that the agent actually produced reviews for during development.

## How it works

1. CLI fetches the PR metadata and the raw `.diff` from the GitHub API.
2. The diff is truncated to 60k characters to stay within Claude's context window.
3. A single Claude call (model: `claude-opus-4-7`) with a strict system prompt returns JSON: `{summary, risks, suggestions, confidence}`.
4. The JSON is rendered to Markdown (or returned as-is with `--json`).

## File layout

```
claude-review/
├── README.md                       # this file (combined with main repo README)
├── action.yml                      # composite GitHub Action
├── requirements.txt                # empty — stdlib only
├── claude_review/
│   ├── __init__.py                 # main module — review logic
│   └── __main__.py                 # `python -m claude_review` entry point
└── examples/
    ├── workflow.yml                # example GitHub workflow using the action
    ├── PR-strict-kwargs-201.md     # sample review
    └── PR-anyformat-workshop-39.md # sample review
```

## License

MIT
