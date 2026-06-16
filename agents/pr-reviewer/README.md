# PR Reviewer — structured Markdown PR review agent

A Claude Code agent that takes a pull-request diff as input, analyzes it, and
returns a single, structured Markdown review comment:

- **📝 Summary** — what the PR changes, in 2–3 sentences
- **⚠️ Risks** — concrete bugs/concerns, each tagged `[High] / [Medium] / [Low]`
- **💡 Suggestions** — optional, actionable improvements
- **✅ Confidence** — `Low / Medium / High` with a one-line rationale

It runs three ways, all sharing one prompt
([`prompts/review-system-prompt.md`](prompts/review-system-prompt.md)):

| Mode | Engine | Use it for |
|------|--------|-----------|
| **CLI** (`bin/pr-review`) | `claude` CLI *or* Anthropic API | Local reviews from your terminal |
| **Native agent** (`.claude/agents/pr-reviewer.md`) | Claude Code | `@pr-reviewer` inside Claude Code |
| **GitHub Action** (`github-action/pr-review.yml`) | Anthropic API | Auto-review + comment on every PR |

> **Built for bounty [#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)** — "AGENT: PR reviewer with structured Markdown output".

---

## Repository layout

```
agents/pr-reviewer/
├── README.md                       # this file
├── requirements.txt                # anthropic SDK (for the API engine)
├── prompts/
│   └── review-system-prompt.md     # single source of truth for the review
├── .claude/agents/
│   └── pr-reviewer.md              # native Claude Code subagent definition
├── scripts/
│   └── pr_review.py                # portable reviewer (Anthropic API)
├── bin/
│   └── pr-review                   # CLI wrapper (diff acquisition + engine)
├── github-action/
│   └── pr-review.yml               # workflow — copy to .github/workflows/
└── samples/
    ├── pr-1-flask-6013.md          # real output: pallets/flask#6013
    └── pr-2-requests-7502.md       # real output: psf/requests#7502
```

---

## Quick start (CLI)

```bash
cd agents/pr-reviewer

# Review a GitHub PR by URL or number (uses the `gh` CLI to fetch the diff):
./bin/pr-review --pr https://github.com/pallets/flask/pull/6013

# Review the current branch against main:
git diff origin/main...HEAD | ./bin/pr-review

# Review a patch file and save the result:
./bin/pr-review --diff my-change.patch --out review.md
```

### Picking an engine

`bin/pr-review` auto-selects an engine, or you can force one with `--engine`:

- **`--engine claude`** (default when the [`claude` CLI](https://docs.claude.com/en/docs/claude-code)
  is installed) — runs the review through `claude -p`. No API key needed beyond
  your existing Claude Code auth.
- **`--engine api`** (default otherwise) — runs `scripts/pr_review.py` against
  the Anthropic API. Requires `ANTHROPIC_API_KEY` and `pip install -r requirements.txt`.

```bash
./bin/pr-review --pr 6013 --engine api      # force the API engine
./bin/pr-review --pr 6013 --engine claude   # force the Claude Code engine
```

---

## Setup

### Prerequisites
- [`gh`](https://cli.github.com/) (GitHub CLI) — only needed for `--pr`.
- **One** of:
  - the [`claude` CLI](https://docs.claude.com/en/docs/claude-code) (for the `claude` engine), or
  - Python 3.9+ with `ANTHROPIC_API_KEY` (for the `api` engine).

### API engine install
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
# Optional: override the model (defaults to claude-sonnet-4-6)
export PR_REVIEW_MODEL="claude-sonnet-4-6"
```

The script can be run directly too:
```bash
python scripts/pr_review.py --pr 7502 --title "Fix file detection"
cat my.patch | python scripts/pr_review.py
```

---

## Use it as a native Claude Code agent

Copy the agent definition so Claude Code can discover it:

```bash
# project-local
mkdir -p .claude/agents && cp agents/pr-reviewer/.claude/agents/pr-reviewer.md .claude/agents/
# or user-global
cp agents/pr-reviewer/.claude/agents/pr-reviewer.md ~/.claude/agents/
```

Then, inside Claude Code:

```
> review PR 6013 with the pr-reviewer agent
> @pr-reviewer review the current branch
```

The agent knows how to fetch the diff itself (`gh pr diff`, a pasted diff, or
`git diff`) and emits the same four-section format.

---

## Use it as a GitHub Action

1. Copy the workflow into your repo:
   ```bash
   mkdir -p .github/workflows
   cp agents/pr-reviewer/github-action/pr-review.yml .github/workflows/
   ```
   (The workflow references `agents/pr-reviewer/...`, so keep this folder in the
   repo, or adjust the paths in the YAML.)
2. Add an `ANTHROPIC_API_KEY` repository secret
   (**Settings → Secrets and variables → Actions**).
3. Open or update a PR. The action fetches the diff, runs the reviewer, and
   posts a **single sticky comment** that it updates on each push (matched by a
   hidden `<!-- pr-reviewer-agent -->` marker).

It runs with least privilege: `contents: read`, `pull-requests: write`.

---

## Output format

Every engine emits exactly these four sections, in order:

```markdown
## 📝 Summary
<2–3 sentences>

## ⚠️ Risks
- **[High]** <concrete risk, cites file/symbol>
- **[Medium]** ...

## 💡 Suggestions
- <one-line improvement>

## ✅ Confidence
**Medium** — <one sentence of rationale>
```

See [`samples/`](samples/) for two complete, real outputs.

---

## Sample outputs (tested on real PRs)

Both files below are **verbatim output** from the live `claude` engine, run on
these real merged PRs:

| # | PR | Diff | Result |
|---|----|------|--------|
| 1 | [pallets/flask#6013](https://github.com/pallets/flask/pull/6013) | +6/−1 | [`samples/pr-1-flask-6013.md`](samples/pr-1-flask-6013.md) — **High** confidence |
| 2 | [psf/requests#7502](https://github.com/psf/requests/pull/7502) | +14/−1 | [`samples/pr-2-requests-7502.md`](samples/pr-2-requests-7502.md) — **High** confidence, flags a real `[Medium]` edge case |

Reproduce:
```bash
gh pr diff https://github.com/pallets/flask/pull/6013  | ./bin/pr-review --engine claude
gh pr diff https://github.com/psf/requests/pull/7502   | ./bin/pr-review --engine claude
```

---

## Design notes

- **One prompt, three runners.** The CLI, the native agent, and the Action all
  use `prompts/review-system-prompt.md`, so behavior stays consistent and there
  is a single place to tune the rubric.
- **Honest, proportionate reviews.** The prompt forbids manufacturing risks: a
  small clean diff gets a short review and a **High** score. Confidence is
  explicitly lower when the diff depends on code it cannot see.
- **Diff-only analysis.** The reviewer is told to judge only what the diff shows
  and to flag when missing context limits its confidence, rather than inventing
  behavior.
- **Safety guardrails.** The API script caps diffs at 200k chars (noting the
  truncation in the prompt) and fails with clear, CI-friendly messages on
  missing keys, empty diffs, or `gh` errors.

## Limitations
- Reviews are **advisory** — they assist human reviewers, they don't replace them.
- Analysis is limited to the diff; whole-repo reasoning is out of scope.
- Very large PRs are truncated; split them or raise `MAX_DIFF_CHARS`.

## License
MIT, per the repository [LICENSE](../../LICENSE).
