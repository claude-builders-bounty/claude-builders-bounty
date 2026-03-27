# PR Review Sub-Agent

Claude Code skill that reviews GitHub pull requests with structured feedback.

## Setup

```bash
cp review-pr.md /path/to/project/.claude/skills/review-pr.md
```

## Usage

```
/review-pr 42
/review-pr https://github.com/org/repo/pull/42
```

## What It Checks

| Category | Examples |
|----------|---------|
| 🐛 Bugs | Logic errors, null handling, race conditions |
| 🔒 Security | SQL injection, XSS, hardcoded secrets |
| ⚡ Performance | N+1 queries, unnecessary re-renders |
| 🎨 Style | Naming, dead code, complexity |

## Output

Structured Markdown with file:line references, categorized issues, and a verdict (Approve / Request Changes / Needs Discussion).

## Requirements

- `gh` CLI authenticated (`gh auth status`)
- Run from within a git repository
