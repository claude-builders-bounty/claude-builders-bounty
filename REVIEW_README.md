# claude-review

Autonomous PR reviewer for Claude Code. Analyzes GitHub PRs and returns structured Markdown review with risk assessment and improvement suggestions.

## Installation

```bash
cp claude-review /usr/local/bin/
chmod +x /usr/local/bin/claude-review
export GH_TOKEN="your_github_token"
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## What it checks

| Category | Patterns detected |
|----------|------------------|
| Credentials | Hardcoded secrets, passwords, API keys |
| Destructive SQL | DROP TABLE, DROP DATABASE, TRUNCATE |
| Dangerous commands | Recursive force delete |
| Debug artifacts | Console.log, debug statements |
| Unresolved markers | TODO, FIXME, HACK, XXX |
| PR size | Files changed > 15, additions > 500 |

## Output format

Structured Markdown with:
- **Summary** — lines changed, files touched
- **Identified Risks** — security concerns, code quality issues
- **Improvement Suggestions** — testing, dependencies, edge cases
- **Assessment** — Confidence score (Low/Medium/High) with reasoning

## Sample outputs

### Test 1: Documentation PR (Low risk)
`claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1699`

```
# PR Review: feat: add opinionated CLAUDE.md for Next.js 15 + SQLite SaaS

PR: claude-builders-bounty/claude-builders-bounty#1699
Summary: Adds 97 lines, removes 1 lines across 1 file(s).

## Identified Risks
- ✅ No obvious risks detected.

## Assessment
Confidence: High — No risky patterns detected. Changes appear focused and well-scoped.
```

### Test 2: Payment Integration PR (Detected risks)
`claude-review --pr https://github.com/SecureBananaLabs/bug-bounty/pull/2`

```
## Identified Risks
- ⚠️ Credentials: File contains strings matching 'secret', 'password', or 'token'.
- 🔶 Unresolved markers: TODO/FIXME/HACK comments present.

## Assessment
Confidence: Low — Significant concerns (4 risk points). Manual review strongly recommended.
```
