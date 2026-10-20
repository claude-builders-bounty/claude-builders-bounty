# 🕵️ Claude Code PR Review Sub-Agent CLI & GitHub Action

Automated Pull Request reviewer that inspects diffs, evaluates security risks (OWASP, hardcoded secrets, dangerous execution patterns), verifies test coverage, and outputs structured Markdown review comments.

---

## 🚀 Setup & Usage Instructions

### Method 1: Local CLI Execution
```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```
*Optional parameters:*
- `--token YOUR_GITHUB_TOKEN`: For private repositories or increased rate limits.
- `--output review.md`: Writes formatted markdown directly to a file.

---

### Method 2: GitHub Action Integration
Copy `pr-review-agent.yml` into your repository at `.github/workflows/pr-review.yml`. It will automatically trigger on newly opened or synchronized pull requests and post a structured review comment.

---

## 📋 Structured Output Format
- **Summary of Changes**: 2-3 sentence overview of scope, delta, and modified components.
- **Identified Risks**: Security vulnerabilities, regression risks, large diff warnings.
- **Improvement Suggestions**: Actionable architectural and testing recommendations.
- **Confidence Score**: Low / Medium / High.

See `sample_review_1.md` and `sample_review_2.md` for verified output examples.
