# open-reviewer

A **multi-agent orchestration system** for AI-powered GitHub PR reviews, built on OpenClaw. Coordinates a team of specialized sub-agents to produce in-depth, structured Markdown reviews.

## Architecture

```
claude-review → Main Review Coordinator
             ├── Security Reviewer   (dedicated security analysis)
             ├── Code Quality Reviewer (dedicated quality analysis)
             └── returns unified structured Markdown report
```

## Three ways to use

### 1. Claude Code sub-agent (recommended)

```bash
# Copy agent definitions into your project
mkdir -p .claude/agents/reviewers
cp -r agents/open-reviewer/.claude/agents/reviewers .claude/agents/
cp agents/open-reviewer/.claude/agents/review-coordinator.md .claude/agents/
```

Then ask Claude Code to review:
> `"Review https://github.com/owner/repo/pull/123"`

### 2. CLI

```bash
python agents/open-reviewer/bin/claude-review.py --pr <url> [--post] [--json]
```

### 3. GitHub Action

```bash
mkdir -p .github/workflows
cp agents/open-reviewer/workflows/pr-review.yml .github/workflows/
```

Add `ANTHROPIC_API_KEY` to repo secrets (optional — heuristic mode works without it).

## What makes it different

Unlike single-script reviewers, `open-reviewer` uses a **multi-agent team**:

| Agent | Responsibility |
|---|---|
| **Review Coordinator** | Orchestrates the review, synthesizes all findings into the final report |
| **Security Reviewer** | Scans for hardcoded secrets, injection risks, CVEs, unsafe patterns |
| **Code Quality Reviewer** | Evaluates maintainability, testing gaps, error handling, architectural concerns |

Each reviewer agent operates in its own context, producing domain-specific findings that the coordinator merges into a single structured report.

## Review output format

```markdown
## Claude Review

**PR:** #123 — Add feature X
**Reviewers:** security-reviewer, code-quality-reviewer
**Generated:** 2026-05-10

### Summary

### Security Analysis
> [security-reviewer]

### Code Quality Analysis
> [code-quality-reviewer]

### Combined Risks
<!-- risk items from both reviewers -->

### Improvement Suggestions
<!-- merged from both reviewers -->

### Confidence Score
| Factor | Score |
|---|---|
| Base | 0.85 |
| Security findings | -0.10 |
| Quality gaps | -0.05 |
| Final | 0.70 → **Medium** |
```

## Real samples

Run the samples yourself:
```bash
python agents/open-reviewer/bin/claude-review.py \
  --pr https://github.com/psf/requests/pull/7401
python agents/open-reviewer/bin/claude-review.py \
  --pr https://github.com/astral-sh/uv/pull/19322
```

## Tests

```bash
python agents/open-reviewer/tests/test_review.py -v
```