# claude-review — Structured PR Code Review Agent

AI-powered pull request code review agent for Claude Code.

## Installation (2 steps)
```bash
chmod +x claude-review
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

### CLI
```bash
./claude-review --pr https://github.com/SecureBananaLabs/bug-bounty/pull/75
./claude-review --pr URL --output review.md
```

### GitHub Action
Copy `.github/workflows/claude-review.yml` to your repo.

## Output Sections

| Section | Content |
|---------|---------|
| Summary of changes | 2-3 sentence overview |
| Identified risks | List of detected issues (credentials, debug output, etc.) |
| Improvement suggestions | Optional enhancements |
| Confidence score | Low / Medium / High |

## Test Results

Tested on 2 real PRs:

**PR #1: SecureBananaLabs/bug-bounty#75 (Stripe SDK)**
- Files: 5, +277/-12
- Risks: 2 (TODO comments, credential patterns)
- Confidence: Medium

**PR #2: claude-builders-bounty#1600 (Safety Hook)**
- Files: 3, +211/-48
- Risks: 1 (debug output)
- Confidence: Medium
