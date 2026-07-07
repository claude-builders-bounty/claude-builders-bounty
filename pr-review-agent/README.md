# Claude PR Review Agent (Bounty #4)

An elite, automated PR Review Agent powered by Claude 3.5 Sonnet. This agent acts as a senior staff software engineer, providing deep, structured code reviews directly on your Pull Requests.

## Features
- **CLI Mode:** Run it locally against any public GitHub PR.
- **GitHub Action Mode:** Runs automatically on every Pull Request in your repository.
- **Highly Structured Output:** Markdown format including PR Overview, Summary, Severity-Rated Risks, Suggestions, and a Confidence Score.

## 🚀 Quick Start (CLI)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API Keys:**
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export GITHUB_TOKEN="your-github-token" # Optional, but recommended to avoid rate limits
   ```

3. **Run the Reviewer:**
   ```bash
   python claude-review.py --pr https://github.com/owner/repo/pull/123
   ```

   *To save the output to a file:*
   ```bash
   python claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
   ```

## 🤖 GitHub Action Setup

To fully automate this across your repository, just copy the workflow file into your `.github` directory.

1. **Copy the workflow:**
   Copy `.github/workflows/pr-review.yml` into your repository.

2. **Add the Repository Secret:**
   Go to your repository settings -> **Secrets and variables** -> **Actions**.
   Add a new repository secret named `ANTHROPIC_API_KEY` with your actual key.

3. **Profit!**
   Every time a Pull Request is opened or updated, the action will trigger, call Claude, and post the review as a comment automatically.
