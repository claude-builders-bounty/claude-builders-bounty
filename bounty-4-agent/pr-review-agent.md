# PR Review Agent — Claude Code Sub-agent

## Overview
A Claude Code sub-agent that reviews a GitHub PR diff and posts a structured markdown comment.

## How to Use
```bash
claude-code --agent pr-review -- "Review this PR diff"
```

Or as a pipe:
```bash
curl -s https://api.github.com/repos/owner/repo/pulls/123 | claude-code --stdin --agent pr-review
```

## Agent Instructions

When invoked as a PR review agent, follow these steps:

### Step 1: Extract PR Information
Parse the input to identify:
- Repository (owner/name)
- PR number
- Base branch and head branch
- Title and description

### Step 2: Fetch the Diff
Use `gh pr view <number> --json diff,comments,files` or
`curl https://api.github.com/repos/owner/repo/pulls/<number>`
to get the actual code changes.

### Step 3: Analyze
Review for:
- **Correctness**: Logic errors, edge cases, race conditions
- **Security**: Injection, auth bypass, data exposure
- **Performance**: N+1 queries, memory leaks, unnecessary computations
- **Maintainability**: Complexity, duplication, naming, test coverage
- **Style**: Consistency with project conventions

### Step 4: Post Structured Review
Format the review as:

```markdown
## PR Review: <title>

### Summary
<1-2 sentence overall assessment>

### Files Changed
| File | Lines | Status |
|------|-------|--------|
| path/to/file.ts | +10/-2 | modified |

### Findings

#### 🔴 Critical (must fix)
- **file.ts:42** — Description of the issue and fix suggestion

#### 🟡 Warning (should fix)
- **file.ts:88** — Description of the concern

#### ℹ️ Suggestion
- **file.ts:120** — Optional improvement idea

### ✅ What's Good
- Notes on things done well

### Score
**Approve / Request Changes / Comment** based on findings.
```

### Installation
Place this file in your project as `.claude/agents/pr-review.md`.
Then run: `claude-code --agent pr-review -- "gh pr view 123"`
