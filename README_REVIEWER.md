# Claude Code PR Reviewer Agent

An automated, intelligent Pull Request reviewer agent designed for Claude Code and GitHub Actions.

## 🚀 Quick Setup (3 Steps)

### Step 1: Install Dependencies
```bash
python -m pip install --upgrade urllib3
```

### Step 2: Run CLI Review on Any PR
```bash
python claude_review.py --pr "https://github.com/owner/repo/pull/123"
```

Or review a local diff file:
```bash
python claude_review.py --diff-file changes.diff
```

### Step 3: Enable Automated GitHub Action
Copy `.github/workflows/pr-review.yml` into your repository. The workflow will automatically post structured reviews on every new PR!
