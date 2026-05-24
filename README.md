# Git Changelog Generator

A simple and robust bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Features
- Fetches commits since the last git tag (or from the initial commit if no tags exist).
- Auto-categorizes commits into `Added`, `Fixed`, `Removed`, and `Changed` based on conventional commit prefixes.
- Outputs a cleanly formatted `CHANGELOG.md` file.

## Setup Instructions

1. **Download the script** into your repository:
   ```bash
   curl -O https://raw.githubusercontent.com/Ishant5436/claude-builders-bounty/main/changelog.sh
   ```
2. **Make it executable**:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run it**:
   ```bash
   ./changelog.sh
   ```

This will instantly generate a `CHANGELOG.md` in your current directory.

---

# Claude PR Reviewer Agent

A Python CLI agent that analyzes a GitHub Pull Request diff and generates a structured Markdown review using the Anthropic API.

## Features
- Fetches the PR diff directly using the GitHub CLI (`gh`).
- Uses `claude-3-5-sonnet` to generate a structured review.
- Outputs a Summary, Identified Risks, Improvement Suggestions, and a Confidence Score.

## Setup Instructions

1. **Install dependencies** (Requires Python 3 and the GitHub CLI):
   ```bash
   # Ensure you are logged into the GitHub CLI
   gh auth login
   ```
2. **Set your API Key**:
   ```bash
   export ANTHROPIC_API_KEY="your_claude_api_key"
   ```
3. **Run the script**:
   ```bash
   ./claude-review.py --pr https://github.com/owner/repo/pull/123
   ```

---

# n8n Weekly Dev Summary Workflow

An automated n8n workflow that fetches a repository's weekly activity (commits, closed issues, merged PRs) and uses Claude to post a narrative summary to Discord.

## Setup Instructions (4 Steps)

1. **Import the Workflow**: Open your n8n dashboard, click **Add Workflow** -> **Import from File**, and select `weekly-dev-summary-workflow.json`.
2. **Set Configuration Variables**: Open the `Config` node and update `github_repo` (e.g. `owner/repo`), `discord_webhook_url`, and `language` (e.g. `EN` or `FR`).
3. **Add Anthropic Credentials**: Open the `Call Claude` HTTP Request node, create a new "Header Auth" credential, and paste your `ANTHROPIC_API_KEY`.
4. **Activate**: Toggle the workflow switch to **Active**. It will automatically execute every Friday at 5 PM!
