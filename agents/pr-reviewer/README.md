# pr-reviewer

A Claude Code sub-agent + CLI + drop-in GitHub Action that reads a GitHub
pull request, runs deterministic heuristics, optionally polishes the prose
with the Claude API, and emits a structured Markdown review with summary,
risks, suggestions, and a principled confidence score. Closes [#4](../../issues/4).

```
agents/pr-reviewer/
├── README.md                       ← you are here
├── claude_review.py                ← single-file CLI (Python 3 stdlib only)
├── .claude/agents/pr-reviewer.md   ← Claude Code sub-agent definition
├── workflows/pr-review.yml         ← drop-in GitHub Action
├── samples/
│   ├── pr-requests-7401.md         ← real review of psf/requests #7401
│   └── pr-uv-19322.md              ← real review of astral-sh/uv #19322
└── tests/test_review.py            ← 26 unittest cases (no deps)
```

## Three ways to invoke

### 1. CLI

```bash
# Default hybrid mode: heuristics + LLM polish if ANTHROPIC_API_KEY is set,
# falls back to heuristic-only otherwise.
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123

# Heuristic-only (deterministic, no API calls)
python agents/pr-reviewer/claude_review.py --pr <url> --mode heuristic

# LLM-only (skip heuristics)
ANTHROPIC_API_KEY=sk-... python agents/pr-reviewer/claude_review.py --pr <url> --mode llm

# Write to file
python agents/pr-reviewer/claude_review.py --pr <url> --output review.md --quiet

# JSON envelope for tooling
python agents/pr-reviewer/claude_review.py --pr <url> --json

# Post the review back to the PR as a comment (idempotent: edits the same
# comment on subsequent runs instead of spamming new ones).
python agents/pr-reviewer/claude_review.py --pr <url> --post
```

GitHub auth resolves in this order: `--github-token` flag → `GITHUB_TOKEN` /
`GH_TOKEN` env → `gh auth token`. Anthropic auth: `--anthropic-key` flag →
`ANTHROPIC_API_KEY` env.

### 2. Claude Code sub-agent

Copy the agent definition into your project:

```bash
mkdir -p .claude/agents
cp agents/pr-reviewer/.claude/agents/pr-reviewer.md .claude/agents/
```

Then ask Claude Code to review a PR:

> "Review https://github.com/owner/repo/pull/123"

Claude Code routes to the `pr-reviewer` sub-agent, which calls the CLI and
returns the rendered Markdown verbatim.

### 3. GitHub Action (drop-in)

```bash
mkdir -p .github/workflows
cp agents/pr-reviewer/workflows/pr-review.yml .github/workflows/
```

Add `ANTHROPIC_API_KEY` to your repo's secrets (optional — heuristic mode
works without it). Push, open a PR, and the bot posts a review comment.
**Idempotent** — subsequent commits edit the same comment via a hidden
HTML marker (`<!-- claude-review-bot:do-not-remove -->`), no comment spam.

## What the review contains

| Section | Source |
|---|---|
| **Summary** — what changed and apparent intent | LLM (or heuristic fallback) |
| **Risks** — high/critical findings, cited as `file:line` | Heuristics + LLM |
| **Suggestions** — concrete improvements, copy-pasteable | Heuristics + LLM |
| **Confidence** — High / Medium / Low + numeric score | Principled formula |

### Heuristic categories

| Severity | Category | Examples |
|---|---|---|
| 🚨 critical | security | hardcoded AWS / OpenAI / GitHub token literals, `api_key = "..."` patterns |
| ⚠️ high | risk | `eval(`, `shell=True`, `dangerouslySetInnerHTML`, `DROP TABLE`, `DELETE FROM` without `WHERE` |
| 🟡 medium | hygiene / size / testing | dev-only files committed (`.env.local`, `.vscode`), 1000+ line files, source changes without tests |
| 🔵 low | hygiene | `console.log`, `print(`, `debugger`, `binding.pry` |
| ℹ️ info | docs / dependencies | empty PR description, `package.json` / `requirements.txt` changed |

### Confidence formula

```
score = 0.9
       - 0.45 if delta > 1500 lines
       - 0.25 if delta > 500   (else -0.10 if delta > 150)
       - 0.25 × min(critical_findings, 3)
       - 0.10 × min(high_findings, 4)
       - 0.10 if PR description is empty
clamp to [0.05, 0.95]

>= 0.70  →  High
>= 0.40  →  Medium
<  0.40  →  Low
```

A 700-line clean diff lands at Medium (45%); a 50-line diff with a
critical security finding lands at Low; a 50-line clean diff with a real
PR description lands at High (90%).

## Real samples

Both files committed in `samples/` and reproducible from any machine with
Python 3 and a GitHub token:

- [`samples/pr-requests-7401.md`](samples/pr-requests-7401.md) — psf/requests
  #7401, 13-line test addition. Output: **High (90%) confidence, no risks**.
- [`samples/pr-uv-19322.md`](samples/pr-uv-19322.md) — astral-sh/uv #19322,
  2818-line "Sync latest Python releases" diff. Output: **Medium (45%)**,
  flags missing-tests + a 1000+ line vendored JSON file + the overall
  size as risks. Confidence reason: "Large diff is the dominant
  uncertainty driver."

Reproduce:

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/psf/requests/pull/7401 --mode heuristic
python agents/pr-reviewer/claude_review.py --pr https://github.com/astral-sh/uv/pull/19322 --mode heuristic
```

## Tests

```bash
python agents/pr-reviewer/tests/test_review.py -v
# Ran 26 tests in 0.01s — OK
```

26 unittest cases covering:
- PR URL parsing (canonical, trailing slash, rejection of non-PR URLs)
- Unified diff line accounting across multiple hunks
- Each heuristic category with real-world positive + negative cases
- Confidence-score buckets (High / Medium / Low) for representative inputs
- Markdown rendering (marker present, sections present, LLM body precedence)
- CLI integration via mocked `fetch_pr` (heuristic mode, JSON envelope,
  LLM-without-key error path)

## Design choices

- **Single-file CLI, stdlib only.** No `pip install` for heuristic mode. LLM
  mode also stdlib — uses `urllib` to call `api.anthropic.com` directly with
  prompt caching on the system prompt.
- **Hybrid by default.** Heuristics give file:line specificity the LLM
  doesn't reliably produce; the LLM gives prose summary the heuristics can't
  produce. Hybrid feeds heuristic findings into the LLM prompt and lets the
  LLM dismiss false positives explicitly.
- **Idempotent commenting.** A hidden HTML marker lets the GitHub Action
  edit the existing review comment on every push instead of cluttering the
  PR with a new comment per commit.
- **Graceful degradation.** No `ANTHROPIC_API_KEY` → heuristic-only review
  with a `mode: heuristic` indicator in the header. LLM call fails → warning
  to stderr, falls back to heuristic. Never crashes on missing config.
- **Principled confidence.** The score is a single transparent formula
  documented above; no black-box scoring.

## Acceptance criteria checklist

- [x] CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action workflow YAML included
- [x] Structured Markdown output with summary, risks, suggestions, confidence
- [x] Tested on 2 real GitHub PRs with outputs included in `samples/`
- [x] README with setup and usage instructions
