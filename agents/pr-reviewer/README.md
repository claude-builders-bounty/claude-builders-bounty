# pr-reviewer — Claude Code sub-agent that reviews PRs

A self-contained Claude Code sub-agent + CLI + GitHub Action that takes a PR diff and emits a structured Markdown review comment with **Summary**, **Risks**, **Improvement suggestions**, and a **Low / Medium / High confidence** score.

## Output shape (always exactly this)

```markdown
## Summary
2–3 sentences on what the PR is about and the change shape.

## Risks
- One bullet per risk (or `- _none identified_`)

## Improvement suggestions
- One bullet per suggestion (or `- _none_`)

**Confidence:** Low | Medium | High
```

## Three ways to use it

### 1. CLI

```sh
# Review by PR URL (uses GITHUB_TOKEN to fetch the diff)
python agents/pr-reviewer/bin/claude-review.py --pr https://github.com/owner/repo/pull/123

# Review a piped diff
git diff main...feature | python agents/pr-reviewer/bin/claude-review.py --stdin

# Review a saved diff file
python agents/pr-reviewer/bin/claude-review.py --diff-file pr.diff

# Post the review back as a PR comment
python agents/pr-reviewer/bin/claude-review.py --pr <url> --post
```

### 2. GitHub Action

Drop [`agents/pr-reviewer/.github/workflows/pr-review.yml`](.github/workflows/pr-review.yml) into your repo's `.github/workflows/` directory and add `ANTHROPIC_API_KEY` to repo secrets. Every PR will get a Claude review comment automatically.

### 3. Inside Claude Code

The agent is defined in [`AGENT.md`](AGENT.md). When asked to review a PR, Claude Code can invoke this sub-agent and produce the same structured output without leaving the session.

## Auth model (priority order)

| Path                | When used                                                               |
|---------------------|-------------------------------------------------------------------------|
| `ANTHROPIC_API_KEY` | Direct Anthropic API call. Used in CI / GitHub Actions.                  |
| `claude` CLI        | Falls back to the user's locally-logged-in Claude Code (OAuth).          |
| `GITHUB_TOKEN`      | Used to fetch PR metadata + the unified diff. Falls through to `gh` CLI. |

## Confidence-score rules (so reviewers can triage)

- **High** — small (<200 LOC), self-contained, mechanical change (rename / dep bump / format) where the diff is its own justification.
- **Medium** — a real change with adequate test coverage in the diff.
- **Low** — large (>1000 LOC), missing context (private deps, no tests in diff), or multiple unrelated changes bundled.

## Sample outputs

Generated against real public PRs (no mocks). Diffs were fetched live; the review output is verbatim.

- [`samples/sample-1.md`](samples/sample-1.md) — review of [tscircuit/circuitjson.com#122](https://github.com/tscircuit/circuitjson.com/pull/122) — a 13-package dep bump + lockfile deletion. Confidence: Low. The agent correctly flagged the missing lockfile replacement as the primary risk.
- [`samples/sample-2.md`](samples/sample-2.md) — review of [tari-project/wxtm-bridge-frontend#127](https://github.com/tari-project/wxtm-bridge-frontend/pull/127) — a two-line CVE-mitigation pin. Confidence: High. The agent correctly identified the lockfile-regen gap that the PR author had already documented.

## Acceptance-criteria mapping (issue #4)

| Criterion                                                              | Where                                                          |
|-------------------------------------------------------------------------|----------------------------------------------------------------|
| Works via CLI: `claude-review --pr <url>`                              | `bin/claude-review.py` with `--pr` flag                        |
| OR via GitHub Action (workflow YAML)                                    | `.github/workflows/pr-review.yml`                              |
| Structured Markdown output                                              | `PROMPT_TEMPLATE` in `bin/claude-review.py` + `AGENT.md`        |
| - Summary (2–3 sentences)                                               | enforced by prompt                                             |
| - Identified risks (list)                                               | enforced by prompt                                             |
| - Improvement suggestions (list)                                        | enforced by prompt                                             |
| - Confidence score: Low / Medium / High                                 | enforced by prompt + scoring rubric in this README + AGENT.md  |
| Tested on at least 2 real GitHub PRs (outputs in PR)                    | `samples/sample-1.md` + `samples/sample-2.md`                  |
| README with setup and usage                                             | this file                                                      |

## Limitations / known gotchas

- **Diff truncation.** Diffs over 60 KB are truncated to fit a single Claude turn. The agent escalates Confidence to Low when this happens. If you need to review a giant PR, split it.
- **No multi-turn dialog.** This is a one-shot review — it doesn't follow up on author replies. Pair it with a human reviewer for back-and-forth.
- **Cost.** Each review is one Sonnet 4.5 call (~6–10K tokens in / ~500 tokens out). On a busy repo, scope the GH Action `if:` clause (e.g. `github.event.pull_request.base.ref == 'main'`).

## License

MIT, matches the parent repo.
