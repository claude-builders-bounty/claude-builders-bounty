# Claude PR Reviewer 🤖

An autonomous sub-agent for Claude Code that analyzes Pull Requests and provides structured, actionable feedback.

## Features
- **Summary**: 2-3 sentence overview of changes.
- **Risks**: Identification of security, performance, and stability risks.
- **Suggestions**: Clear, code-block driven improvements.
- **Confidence Score**: Low / Medium / High assessment.

## Usage
Run directly from Claude Code:
```bash
python3 tools/claude_pr_reviewer.py --pr https://github.com/owner/repo/pull/123
```

## Installation (2 Commands)
```bash
git clone https://github.com/MichaelSovereign/claude-builders-bounty
cd claude-builders-bounty && pip install requests
```

## Logic
The script fetches the `.patch` version of the PR to minimize token usage while retaining all change context. It then instructs the current Claude session to perform the analysis using a specialized prompt template designed for high-quality reviews.
