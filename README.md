# claude-review

A Claude Code sub-agent that reviews a GitHub PR and posts a structured Markdown comment.

## Setup

```bash
# No dependencies needed — uses Node.js built-ins + gh CLI
# Ensure gh is authenticated:
gh auth status
```

## Usage

### CLI

```bash
# Review a PR (output to stdout + file)
./claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as PR comment
./claude-review --pr https://github.com/owner/repo/pull/123 --post
```

### GitHub Action

The included workflow `.github/workflows/claude-review.yml` automatically reviews every new PR and posts the review as a comment.

## Output Format

Every review includes:

1. **Summary** — 2-3 sentence description of what the PR does
2. **Identified Risks** — Security issues, large changes, error handling gaps (with severity: High/Medium/Low)
3. **Improvement Suggestions** — Missing error handling, TODOs, console.logs, type safety
4. **Confidence Score** — High / Medium / Low

## Detection Capabilities

| Category | Detects |
|----------|---------|
| Security | eval(), innerHTML, document.write, hardcoded credentials, shell exec, raw SQL |
| Code quality | Empty catch blocks, missing error handling, TODO/FIXME, console.log, `any` types |
| PR hygiene | Large file changes (>100 lines), massive PRs (>20 files, >500 additions) |

## Sample Outputs

### Sample 1: Documentation PR (vercel/next.js#94536)

```
## PR Review: docs: align redirect comment with website docs

**Author:** @louzhedong
**Changes:** +1 / -0 across 1 file(s)

### Summary
Align the inline redirect comment with the website docs. Touches redirect.ts.
This PR is primarily additive.

### Identified Risks
No significant risks identified.

### Improvement Suggestions
No suggestions — changes look clean.

### Confidence: **High**
```

### Sample 2: Feature PR (claude-builders-bounty#2587)

```
## PR Review: feat: opinionated CLAUDE.md for Next.js 15 + SQLite SaaS

**Author:** @AmitabhainArunachala
**Changes:** +256 / -0 across 1 file(s)

### Summary
Production-ready CLAUDE.md template for Next.js + SQLite SaaS.
Touches CLAUDE.md. This PR is primarily additive.

### Identified Risks
- **Medium**: Large change (256 added lines) — consider splitting (CLAUDE.md)

### Improvement Suggestions
- Async operations without try/catch — consider adding error handling

### Confidence: **Medium**
```

## Requirements

- Node.js 22+
- [gh CLI](https://cli.github.com/) authenticated with repo access
- For GitHub Action: `pull-requests: write` permission

## License

MIT
