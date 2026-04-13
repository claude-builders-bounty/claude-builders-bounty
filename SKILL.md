---
name: pr-review-agent
description: "AI-powered PR review agent. Analyzes GitHub PR diffs and returns structured Markdown review comments with summary, risks, suggestions, and confidence score."
---

# PR Review Agent

Analyze GitHub PR diffs and return structured Markdown review comments.

## Usage

```bash
# Via CLI
python pr_review.py --pr https://github.com/owner/repo/pull/123

# Via GitHub Action
# Add .github/workflows/pr-review.yml to your repo
```

## Features

- Summary of changes (2-3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High
