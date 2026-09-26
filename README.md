# claude-review — Claude Code PR review sub-agent

A Claude Code sub-agent that takes a GitHub pull request (or a local diff),
analyzes it, and returns a **structured Markdown review comment** with:

- **Summary** — 2–3 sentences of what the PR does
- **Risks** — concrete failure modes and regressions
- **Improvement suggestions** — actionable, ranked by impact
- **Confidence** — Low / Medium / High

Built for the [claude-builders-bounty] issue #4 bounty spec: works via CLI
(`claude-review --pr <url>`) **and** via a GitHub Action workflow.

## What's inside

```
.
├── agent/
│   └── SKILL.md                  # Claude Code sub-agent skill (the reviewer)
├── bin/
│   └── claude-review             # CLI entrypoint (bash)
├── .github/
│   └── workflows/
│       └── pr-review.yml         # GitHub Action (reviews any PR)
├── examples/
│   ├── review-pr-94.md           # sample output on a real PR
│   └── review-pr-519.md          # sample output on a real PR
└── README.md
```

## Requirement

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI (`claude`)
  on the machine that runs the review
- `curl` (default on macOS/Linux/Git Bash)

## Usage

### CLI — review any PR

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

### CLI — review a local diff

```bash
claude-review --diff-file /path/to/change.diff
```

### CLI — pipe a diff

```bash
curl -sL "https://github.com/owner/repo/pull/123.diff" | claude-review
```

### GitHub Action

Add the workflow to your repository (`.github/workflows/pr-review.yml`). It
runs on every opened/synchronized PR, computes the diff against the base
branch, and posts the structured review as a PR comment.

Required secret: `ANTHROPIC_API_KEY` (add it in
`Settings → Secrets and variables → Actions`).

## Output format

Every review follows the exact structure below — digestible by humans and bots.

```markdown
## Review of PR #123

### Summary
<2-3 sentences>

### Risks
- <concrete risk, failure mode, regression, security issue>

### Improvement suggestions
- **<Area>** — <actionable suggestion> (`<file>:<line>`)

### Confidence
**<High|Medium|Low>**
```

## How the agent works

1. **Fetches** the pull request diff from the GitHub API (or reads the local diff).
2. **Reads every hunk** — files changed, intent, new APIs, error handling,
   edge cases, backward compatibility.
3. **Analyzes** like a staff engineer: risks are concrete failure modes, not
   style nits; suggestions are ranked by impact.
4. **Emits** the structured markdown above. It never invents file paths or line
   numbers, and it never pads praise.

To use `claude-review` as a sub-agent inside Claude Code, add the `agent/`
folder to your skills directory (or run the skill directly) — the same rubric
is embedded in `bin/claude-review` for standalone use.

## Tested on real PRs

| PR | Repo | Result |
|----|------|--------|
| [#94](https://github.com/ubiquity/uusd.ubq.fi/pull/94) | uusd.ubq.fi | [review-pr-94.md](examples/review-pr-94.md) |
| [#519](https://github.com/ubiquity/ai.ubq.fi/pull/519) | ai.ubq.fi | [review-pr-519.md](examples/review-pr-519.md) |

## License

MIT — see the project LICENSE.