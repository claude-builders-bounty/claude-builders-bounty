# Claude Code PR Reviewer Agent

Automated PR review agent powered by Claude API & deterministic AST analysis. Generates structured, high-signal Markdown review comments.

## Features
- **Structured Output**: Summaries, risks, improvement suggestions, and confidence scores.
- **Dual Mode**: Runs via CLI or GitHub Action.
- **Zero-Token Fallback**: Works locally without API keys via deterministic AST heuristics.

## Quickstart in 3 Steps

### 1. Installation
```bash
git clone https://github.com/samuel1bostanica-arch/claude-builders-bounty.git
cd claude-builders-bounty
pip install -r requirements.txt # Optional
```

### 2. CLI Usage
```bash
# Review a live PR
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Or review a local diff file
python claude_review.py --diff changes.diff --output review.md
```

### 3. GitHub Action Setup
Add `.github/workflows/claude-pr-review.yml` to your repository. Provide `ANTHROPIC_API_KEY` in GitHub repository secrets.

## Sample Outputs
See `sample_reviews/pr_sample_1.md` and `sample_reviews/pr_sample_2.md` for real-world review outputs.
