# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Agents

### AGENT: PR reviewer with structured Markdown output

This agent takes a GitHub Pull Request URL, fetches its diff, and uses Claude to generate a structured review comment. The review includes a summary, identified risks, improvement suggestions, and a confidence score.

#### Setup
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Opire-Dev/claude-bounty-board.git
    cd claude-bounty-board
    ```
2.  **Install dependencies:**
    ```bash
    pip install anthropic requests
    ```
3.  **Set up API Keys:**
    *   **Anthropic API Key:** Obtain an API key from [Anthropic](https://console.anthropic.com/settings/keys) and set it as an environment variable:
        ```bash
        export ANTHROPIC_API_KEY="sk-ant-..."
        ```
    *   **GitHub Token (Optional but Recommended):** For higher rate limits or private repositories, generate a GitHub Personal Access Token (PAT) with `repo` scope and set it:
        ```bash
        export GITHUB_TOKEN="ghp_..."
        ```

#### Usage

**Via CLI:**
Run the `claude_review.py` script with the `--pr` argument pointing to a GitHub PR URL:

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

Example:
```bash
python claude_review.py --pr https://github.com/Opire-Dev/claude-bounty-board/pull/6
```

**Via GitHub Action:**
A GitHub Actions workflow (`.github/workflows/pr_review_action.yml`) is provided.
1.  Add your `ANTHROPIC_API_KEY` as a repository secret named `ANTHROPIC_API_KEY` in your GitHub repository settings.
2.  The workflow will trigger on `pull_request` events (opened, synchronize, reopened) and run the `claude_review.py` script.
3.  The review output will be uploaded as a workflow artifact named `claude-pr-review`.
4.  Optionally, uncomment the "Post PR Review as Comment" step in the YAML to have the review automatically posted as a comment on the Pull Request.

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
