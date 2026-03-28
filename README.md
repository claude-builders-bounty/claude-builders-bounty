# Claude PR Reviewer Agent

A CLI tool that analyzes GitHub PR diffs and generates structured review comments.

**Bounty:** $150 USD via Opire  
**Issue:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Installation

```bash
pip install requests
chmod +x claude_review.py
```

## Usage

```bash
./claude_review.py --pr https://github.com/owner/repo/pull/123
GITHUB_TOKEN=xxx ./claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Features
- Structured Markdown output: summary, risks, improvements, confidence score
- GitHub Action support for automated PR reviews
- No external AI API required — heuristic analysis of diffs

## Test Results

### SwapTrade-Backend #215
```
## PR Review Summary
### Summary: This PR modifies 9 files with 252 additions, 0 deletions.
### Risks: None identified
### Confidence: Medium
```

## License
MIT
