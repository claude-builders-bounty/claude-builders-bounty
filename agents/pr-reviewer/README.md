# Claude Code PR Reviewer Agent

Implements **Opire Bounty #4 ($150 USD)** for `claude-builders-bounty`.

An autonomous sub-agent that ingests pull request diffs, performs deep structural, security, and performance analysis, and outputs a formatted Markdown review comment with a conclusive verdict (`APPROVE` / `REQUEST_CHANGES` / `COMMENT`).

## Features
- **Dual Execution Modes**:
  - **CLI**: `python pr_reviewer.py --pr https://github.com/owner/repo/pull/123 [--post]`
  - **GitHub Actions**: Automated CI review on every pull request opening or update.
- **Structured Findings**:
  - 📋 Summary of changes (2–3 sentences)
  - ⚠️ Identified risks (secrets, destructive calls, excessive blast radius)
  - 💡 Improvement suggestions (tests, logging, typing)
  - 🏁 Final verdict badge (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`)

## CLI Usage
```bash
python agents/pr-reviewer/pr_reviewer.py --pr https://github.com/owner/repo/pull/42
```

## Opire Bounty Payout Details
- **Bounty**: #4 ($150 USD)
- **Contributor**: @huyhoang2k5
- **USDC (Base / EVM)**: `0xa57a66df3c7053FDAb5fD1d72040bc0c5b3455F8`
- **PayPal**: `lnhhoang2k5@gmail.com`
