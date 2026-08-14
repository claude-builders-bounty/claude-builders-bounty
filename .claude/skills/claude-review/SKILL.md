---
name: claude-review
description: Review a public GitHub pull request and produce a structured Markdown report.
---

# Review a pull request

Run `bin/claude-review --pr <public GitHub PR URL>` and inspect the generated
Summary, Identified risks, Improvement suggestions, and Confidence sections.
Treat the report as a triage aid: verify every finding against the diff and run
the repository's own tests before merging.
