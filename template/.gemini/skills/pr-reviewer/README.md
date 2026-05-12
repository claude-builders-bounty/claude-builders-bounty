# pr-reviewer Agent

A Gemini CLI skill that analyzes GitHub PR diffs and provides structured Markdown feedback.

## Features
- Fetches real-time diffs from any public GitHub PR.
- Structured analysis including:
  - High-level summary.
  - Risk assessment (Severity + Description).
  - Actionable improvement suggestions.
  - Confidence scoring.

## Requirements
- `GITHUB_TOKEN` environment variable (optional, but recommended to avoid rate limits).

## Installation

1. Copy the `pr-reviewer` folder to your skills directory.
2. In Gemini CLI, run `/skills reload`.

## Usage

Ask Gemini to review a PR:
`Review this PR: https://github.com/tscircuit/dsn-converter/pull/354`

The agent will automatically fetch the diff and generate the report.
