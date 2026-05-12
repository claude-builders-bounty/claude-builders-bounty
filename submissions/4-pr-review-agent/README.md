# claude-review

A Claude Code PR review agent that analyzes GitHub pull requests for security risks and code quality issues, outputting a structured Markdown review.

## Quick Start

```bash
# 1. Install
git clone https://github.com/lloyd-c137/claude-review.git
cd claude-review
chmod +x claude-review

# 2. Authenticate (must have gh CLI)
gh auth login

# 3. Review any PR
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Features

- 🔍 Fetches PR diff and metadata via GitHub API
- 🔬 Scans for 18+ security patterns (hardcoded secrets, injection, XSS, weak crypto, etc.)
- 📊 Structured output: Summary → Risks → Suggestions → What Looks Good → Confidence Score
- 🚀 Works with any public GitHub repository

## Example Output

```
## 📋 PR Review

**Repository:** `org/repo`
**PR:** #123
**Author:** @user
**Changes:** +42/-10 across 3 file(s)

### Summary
This PR introduces 42 additions and 10 deletions across 3 files.
Analysis found 1 risk(s) (1 high) and 2 suggestion(s).

### ⚠️ Identified Risks
- **[🟠 High]** Hardcoded API key or token (`src/config.js`)

### 💡 Improvement Suggestions
- Unresolved TODO/FIXME marker in code
- Debug logging left in production code

### ✅ What Looks Good
- Appropriate diff size — manageable for review
- More additions than deletions — net positive contribution

**Confidence Score:** Medium — some concerns to address
```

## Requirements

- `gh` (GitHub CLI) — authenticated
- `python3` — for analysis engine
- `bash` — for CLI wrapper

## How It Works

1. Parses the PR URL to extract owner/repo/number
2. Fetches PR metadata and diff via GitHub API
3. Analyzes each added line against security pattern database
4. Generates structured Markdown review

## License

MIT
