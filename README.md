# Claude PR Review Agent

A Claude Code sub-agent that takes a GitHub Pull Request diff as input, analyzes it,
and returns a structured Markdown review comment.

## Features

- CLI tool: `claude-review --pr <PR_URL>`
- GitHub Action workflow included
- Structured Markdown output:
  - Summary of changes (2–3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

## Installation