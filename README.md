# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

## Bounty #4 deliverable: `claude-review`

This repository now includes a small Python CLI agent for
[#4: PR reviewer with structured Markdown output](../../issues/4).

`claude-review` accepts a GitHub pull request URL, fetches the public `.diff`
for that PR, analyzes the changed files and line counts, and prints a
structured Markdown review comment.

The submission also includes a project-level Claude Code subagent definition at
`.claude/agents/pr-reviewer.md`. The subagent uses Claude Code's Markdown
frontmatter format and can draft the same structured review sections inside a
Claude Code session.

### Setup

```bash
python -m pip install -e .
```

The tool has no third-party runtime dependencies.

### Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

You can also run it without installing the console script:

```bash
python -m claude_review.cli --pr https://github.com/owner/repo/pull/123
```

### Output format

The generated Markdown includes:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

### Claude Code subagent

The `pr-reviewer` subagent is available from:

```text
.claude/agents/pr-reviewer.md
```

It is configured to draft a GitHub-ready review comment with the same required
sections. It can use the CLI as a structural first pass and then refine the
review with repository context when requested.

### Sample outputs

The tool was tested against two real GitHub PRs:

- [`samples/pr-1-output.md`](samples/pr-1-output.md)
- [`samples/pr-2-output.md`](samples/pr-2-output.md)

### Validation

```bash
python -m pip install -e . --no-deps
claude-review --help
python -m unittest discover -s tests
python -m py_compile claude_review/cli.py claude_review/__init__.py tests/test_cli.py
python - <<'PY'
from pathlib import Path
text = Path(".claude/agents/pr-reviewer.md").read_text(encoding="utf-8")
assert text.startswith("---\n")
assert "name: pr-reviewer" in text
assert "description:" in text
assert "## Summary of changes" in text
assert "## Confidence score: Low / Medium / High" in text
PY
python -m claude_review.cli --pr https://github.com/python/cpython/pull/135000
claude-review --pr https://github.com/cli/cli/pull/11703
```

### Notes

This is a lightweight diff-review agent. It uses structural heuristics and
public diff metadata, so its output should complement a human review rather
than replace one.

---

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
