# Aletheia PR Reviewer Agent 🤖

An enterprise-grade, lightweight Code Reviewer Agent designed to automatically audit Pull Request diffs using the Gemini API and output clean, highly structured Markdown reviews.

This agent is built as a packaging-ready, composite-compliant utility designed to serve both as a local CLI tool (`claude-review`) and an automated GitHub Action.

---

## 🚀 Key Features

- **Local CLI Execution**: Run audits on any public or private GitHub PR with one simple command.
- **GitHub Action Native**: Easily plug the agent into any CI/CD pipeline using a composite action layout.
- **Structured Markdown Outputs**: Complies strictly with structured formatting rules:
  1. Concise **Summary of Changes** (2-3 sentences).
  2. Bulleted list of **Identified Risks** (e.g. security, performance, logic).
  3. Bulleted list of **Improvement Suggestions** (readability, robust fixes).
  4. Final **Confidence Score** rating (`Low`, `Medium`, or `High`).
- **High-Performance Execution**: Leverages `gemini-2.5-flash` for ultra-fast, context-aware analysis.

---

## 🛠️ CLI Setup & Installation

### 1. Installation
Clone the repository and install the package locally:
```bash
# Clone the repository
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty

# Install using pip (registers the 'claude-review' executable)
pip install .
```

### 2. Credentials Configuration
The agent requires access to the Gemini API and a GitHub token (for private PRs or to post reviews directly back to PR discussion threads). Set these environment variables:

```bash
# Set your Gemini API key (Required)
export GEMINI_API_KEY="your_gemini_api_key_here"

# Set your GitHub PAT (Optional, required for private repos or posting comments)
export GITHUB_TOKEN="your_github_token_here"
```

---

## 💻 CLI Usage

Once installed, use the registered `claude-review` command to review any Pull Request:

```bash
# Review a PR and output structured Markdown to console
claude-review --pr https://github.com/owner/repo/pull/123

# Review a PR without posting the output back to the GitHub PR thread
claude-review --pr https://github.com/owner/repo/pull/123 --no-post

# Customize the model
claude-review --pr https://github.com/owner/repo/pull/123 --model gemini-2.5-flash
```

---

## 🐙 GitHub Action Integration

To run the reviewer agent automatically on every new pull request, add the following workflow to your repository under `.github/workflows/pr-reviewer.yml`:

```yaml
name: 'PR Reviewer Agent'

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write  # Required to post review comments

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Run Aletheia PR Reviewer
        uses: claude-builders-bounty/claude-builders-bounty@bounty-fix-4
        with:
          pr_url: ${{ github.event.pull_request.html_url }}
          gemini_api_key: ${{ secrets.GEMINI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          model: 'gemini-2.5-flash'
```

---

## 🧪 Proof of Work & Verification Outputs

The reviewer agent has been tested on multiple real-world Pull Requests with pristine structured output.

### Test 1: Review Output for [AgentOrchestration PR #3315](https://github.com/orchestration-agent/AgentOrchestration/pull/3315)
```markdown
## Summary of Changes

This Pull Request introduces a new GitHub Actions workflow for publishing Python packages, triggered by releases or manual dispatch. It implements robust validation of Git references to ensure publications only proceed from protected branches (`main`, `develop`) or cryptographically signed tags. Additionally, the PR includes new Python modules for this release validation, their corresponding unit tests, and minor improvements to resource management (for cross-platform compatibility) and metrics handling within the application.

## Identified Risks

*   **Supply Chain Security (Command Injection)**: The `validate_release.py` script executes `git` commands via `subprocess.run`. While `GITHUB_REF` is generally trustworthy, directly using derived `tag_name` without explicit sanitization could pose a command injection risk if a malicious actor could somehow inject characters into the ref name that `git` would interpret as command flags.
*   **Publish Workflow Bypass**: A logic error in `validate_release.py` that incorrectly sets `is_protected=true` for an unauthorized reference could lead to unintended or unverified package publications, despite the `publish` job's `if` condition.
*   **Resource Limit Enforcement**: The conditional import and usage of the `resource` module in `src/agent/sandbox.py` means resource limits are silently skipped on platforms where `resource` is unavailable (e.g., Windows). If resource limiting is a critical security or stability requirement, this trade-off should be explicitly documented or handled differently.
*   **Dependency Reproducibility**: The `publish.yml` workflow uses `uv sync` without an explicit `uv.lock` file being committed to the repository. This means dependencies might not be fully reproducible across builds if new versions are released, potentially introducing unexpected behavior or vulnerabilities.

## Improvement Suggestions

*   **Input Sanitization in `validate_release.py`**: Add explicit validation (e.g., regex checks) for `branch_name` and `tag_name` within `src/cli/validate_release.py` before passing them to `git` commands, to further mitigate potential command injection risks.
*   **Pin `uv.lock` for Reproducibility**: Commit a `uv.lock` file to the repository and update the `uv sync` step in `publish.yml` to `uv sync --locked` to ensure deterministic dependency installations.
*   **Granular GitHub Actions Permissions**: Consider specifying job-level permissions only where necessary. While current workflow-level permissions are duplicated at the job level, refining them to `contents: read` for `validate-ref` and `build`, and then adding `id-token: write`, `attestations: write` for `publish`, can improve the principle of least privilege.
*   **Explicit `stop_timer` Behavior**: In `src/common/metrics.py`, if `stop_timer` is called for a metric that was never started, it currently returns `0.0` silently. Consider adding a log warning or raising an error in such cases to aid debugging.
*   **Add Newline to `BOUNTY.md`**: Add a newline character at the end of `BOUNTY.md` to conform to POSIX standards for text files and avoid "No newline at end of file" warnings.

Confidence Score: High
```

### Test 2: Review Output for [AIgor PR #4](https://github.com/hunki1488-a11y/AIgor/pull/4)
```markdown
This Pull Request introduces two new files to the repository. The first, `.gitignore`, adds standard ignore patterns for Python bytecode, environment variables, and manifest files. The second, `BOUNTY.md`, outlines the details for a specific bounty, including the issue link, target repository, designated solver, EVM payout wallet address, network, and reward amount.

### Identified Risks
*   **Information Exposure**: The `BOUNTY.md` file contains specific project-internal references (issue link, feature branch) and a concrete EVM payout wallet address. If this repository is public, this information becomes publicly available, which could be used for targeted attacks or tracking if not intended.
*   **Operational Dependency**: The static `BOUNTY.md` file creates a hard-coded dependency on a specific wallet address and solver. Manual updates will be required if the solver changes or if the wallet address needs to be rotated, increasing the risk of outdated or incorrect information.
*   **File Formatting Inconsistency**: The `BOUNTY.md` file lacks a newline character at the end, which can cause minor issues with some text editors, linters, or version control systems.

### Improvement Suggestions
*   **Review Bounty Information Visibility**: Consider whether `BOUNTY.md` should be publicly accessible. For internal tracking or sensitive operational details, a private documentation system, internal wiki, or project management tool might be more appropriate than a public repository file.
*   **Standardize File Endings**: Add a newline character to the end of `BOUNTY.md` to ensure consistency with common text file best practices.
*   **Centralize Bounty Management**: For managing multiple bounties, explore using a more dynamic and centralized system (e.g., a project management tool with dedicated bounty features) instead of static Markdown files to improve maintainability and reduce manual overhead.

Confidence Score: High
```
