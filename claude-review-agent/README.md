# Claude Code PR Review Agent 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Bounty](https://img.shields.io/badge/Bounty-%234%20($150)-green.svg)](#)

A Claude Code sub-agent that takes a GitHub PR diff as input, performs security & risk analysis, and outputs structured Markdown review comments.

---

## 🚀 CLI Usage
```bash
# Review any GitHub PR
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Save to output file
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

---

## 👨‍💻 Author
**Rushikesh Garad** ([@rushikeshgarad2024-dev](https://github.com/rushikeshgarad2024-dev))
