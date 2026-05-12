# Claude Code Bounty Hunter Template 🚀

Deploy a production-ready bounty hunting environment in under 60 seconds.

## Quick Start (60s)

1. **Clone this template**:
   ```bash
   git clone <template-url> my-bounty-project
   cd my-bounty-project
   ```

2. **Load Skills**:
   In your Gemini CLI session, run:
   ```bash
   /skills reload
   ```

3. **Verify Protection**:
   Try a safe command to see the hook in action:
   ```bash
   ls
   ```

## Included Tools

### 🛡️ Safety Guard (`safety-guard.skill`)
Prevents accidental execution of destructive commands (e.g., `rm -rf /`, `mkfs`). It intercepts every shell call and requires your confirmation for high-risk patterns.

### 🔍 PR Reviewer (`pr-reviewer.skill`)
Analyzes GitHub PRs instantly. Provide a URL, and it returns a senior-level code review with risk assessment and improvement suggestions.
- **Usage**: `Review this PR: https://github.com/owner/repo/pull/123`

## Environment Setup

- `GITHUB_TOKEN`: Recommended for the PR Reviewer to avoid rate limits.
- `BUN` or `NODE`: Ensure you have a JS runtime installed for the skill scripts.

---
*Optimized for rapid delivery and maximum efficiency.*
