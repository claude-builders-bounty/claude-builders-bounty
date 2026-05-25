# claude-review — AI-Powered PR Review Agent

An AI sub-agent that reviews a GitHub pull request and posts a structured Markdown review comment. Works with Claude Code's Task tool or standalone via CLI.

## Setup (3 steps)

### 1. Install prerequisites

```bash
# Ensure Python 3.8+ and gh CLI are available
python3 --version
gh auth status
```

### 2. Set your LLM API key

```bash
export LLM_API_KEY="your-zhipuai-api-key"
# Optional: customize model and endpoint
# export LLM_MODEL="glm-4-flashx"
# export LLM_API_BASE="https://open.bigmodel.cn/api/paas/v4"
```

### 3. Run the review

```bash
# Print review to stdout
./claude-review --pr owner/repo/pull/123

# Post review as a PR comment
./claude-review --pr owner/repo/pull/123 --post
```

## Usage

```bash
# Full URL
./claude-review --pr https://github.com/owner/repo/pull/123 --post

# Short format
./claude-review --pr owner/repo/pull/123 --dry-run

# Save to file
./claude-review --pr owner/repo/pull/123 --output review.md
```

## Review Format

Every review follows this structure:

| Section | Description |
|---------|-------------|
| **Summary** | 2-3 sentence plain-English summary of changes |
| **Issues Found — Critical** | Security vulnerabilities, data loss, broken builds |
| **Issues Found — Important** | Bugs, performance, missing error handling |
| **Issues Found — Minor** | Style, naming, optional improvements |
| **Suggestions** | Actionable improvement ideas with reasoning |
| **Overall Assessment** | Quality, risk level, merge readiness, confidence score |

## GitHub Action

To run automatically on PRs, add `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Review
on:
 pull_request:
 types: [opened, synchronize]

jobs:
 review:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v4
 - uses: actions/setup-python@v5
 with:
 python-version: '3.11'
 - name: Install gh
 run: |
 type -p gh >/dev/null || (curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt update && sudo apt install gh -y)
 - name: Run review
 env:
 LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
 GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
 run: |
 chmod +x claude-review
 ./claude-review --pr ${{ github.repository }}/pull/${{ github.event.pull_request.number }} --post
```

## Requirements

- Python 3.8+
- `gh` CLI (authenticated)
- LLM API key (ZhipuAI, OpenAI, or compatible provider)

## License

MIT
