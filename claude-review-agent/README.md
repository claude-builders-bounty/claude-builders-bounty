# claude-review

A Claude Code PR review agent. Fetches a GitHub pull request's diff and
returns a structured Markdown review — summary, identified risks,
improvement suggestions, and a confidence score — powered by Claude
(Anthropic API).

Solves [claude-builders-bounty#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

## Setup

```bash
pip install requests anthropic
export ANTHROPIC_API_KEY=sk-ant-...     # required
export GITHUB_TOKEN=ghp_...             # optional: higher rate limit / private repos
chmod +x claude-review
```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Save the review to a file instead of printing it:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Use a different Claude model (defaults to `claude-sonnet-5`):

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --model claude-opus-5
```

## Output format

Every review always has exactly these four sections, in this order:

```markdown
## Summary of changes
(2–3 sentences)

## Identified risks
- ...

## Improvement suggestions
- ...

## Confidence score
Low / Medium / High — one-sentence justification
```

## GitHub Action

`.github/workflows/review-pr.yml` runs `claude-review` on every PR
(opened/synchronize/reopened) and posts the result as a PR comment. Add
`ANTHROPIC_API_KEY` as a repo secret to use it — no other configuration
needed.

## Sample outputs

Tested against 2 real, public GitHub PRs (see `samples/`):

- [`samples/pr39-aegis-dependency-bump.md`](samples/pr39-aegis-dependency-bump.md) — [conchaestradamiguelangel-droid/aegis#39](https://github.com/conchaestradamiguelangel-droid/aegis/pull/39) (open)
- [`samples/pr37-aegis-dependency-bump.md`](samples/pr37-aegis-dependency-bump.md) — [conchaestradamiguelangel-droid/aegis#37](https://github.com/conchaestradamiguelangel-droid/aegis/pull/37) (closed)

Both are small dependency-bump PRs, deliberately chosen as an easy
correctness check: the tool correctly identifies them as low-risk,
single-line changes instead of padding the review with generic filler.
