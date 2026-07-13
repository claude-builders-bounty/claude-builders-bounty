# 🤖 Claude PR Review Agent

AI-powered Pull Request reviewer that uses Claude to analyze GitHub PR diffs and generate structured, actionable code reviews.

## ✨ Features

- **Structured Markdown reviews**: Summary, risks, suggestions, confidence score
- **CLI tool**: Simple `claude-review --pr <URL>` interface
- **GitHub Action**: Automatic reviews on every PR
- **Multiple output formats**: Markdown or JSON
- **Focus modes**: Security, performance, style, bugs, architecture
- **Colored terminal output**: Beautiful, readable reviews in your terminal
- **Verbose mode**: See the analysis process in detail

## 🚀 Quick Start (5 Steps)

### 1. Clone & Install

```bash
git clone https://github.com/your-org/pr-review-agent.git
cd pr-review-agent
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### 3. Run a review

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

### 4. (Optional) Install globally

```bash
pip install -e .
claude-review --pr https://github.com/owner/repo/pull/123
```

### 5. (Optional) Set up GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo and add `ANTHROPIC_API_KEY` to your repository secrets.

## 📖 Usage

### Basic Review

```bash
claude-review --pr https://github.com/facebook/react/pull/28000
```

### Shorthand PR Reference

```bash
claude-review --pr facebook/react#28000
```

### Focus on Security

```bash
claude-review --pr https://github.com/org/repo/pull/42 --focus security
```

### JSON Output

```bash
claude-review --pr https://github.com/org/repo/pull/42 --format json
```

### Save to File

```bash
claude-review --pr https://github.com/org/repo/pull/42 --output review.md
```

### Verbose Mode

```bash
claude-review --pr https://github.com/org/repo/pull/42 --verbose
```

### Private Repos

```bash
export GITHUB_TOKEN="ghp_your_token"
claude-review --pr https://github.com/private-org/repo/pull/10
```

## 🔧 CLI Options

| Option | Description |
|--------|-------------|
| `--pr URL` | PR URL or shorthand (required) |
| `--format` | Output format: `markdown` (default) or `json` |
| `--output FILE` | Save output to file |
| `--focus` | Review focus: `security`, `performance`, `style`, `bugs`, `architecture` |
| `--model` | Claude model (default: `claude-sonnet-4-20250514`) |
| `--github-token` | GitHub token for private repos |
| `--api-key` | Anthropic API key (or set `$ANTHROPIC_API_KEY`) |
| `--verbose` | Show analysis process |
| `--no-color` | Disable colored output |
| `--version` | Show version |

## 🔄 GitHub Action Setup

1. Copy `.github/workflows/pr-review.yml` to your repository
2. Add `ANTHROPIC_API_KEY` to your repository secrets (Settings → Secrets → Actions)
3. The action will automatically review every new PR and post a comment

### Customizing the Action

Edit the workflow file to:
- Change the Claude model
- Add a review focus
- Adjust trigger events
- Modify the comment format

## 📋 Output Format

### Markdown Output

Every review includes:

- **📋 Summary**: 2-3 sentence overview
- **⚠️ Identified Risks**: Potential bugs, security issues, concerns
- **💡 Improvement Suggestions**: Actionable recommendations
- **📊 Confidence Score**: Low / Medium / High with explanation
- **📁 File-by-File Notes**: Key observations per file

### JSON Output

```json
{
  "pr": {
    "url": "...",
    "title": "...",
    "author": "...",
    "repository": "owner/repo",
    "stats": { "additions": 42, "deletions": 10, "changed_files": 3 }
  },
  "review": {
    "summary": "...",
    "risks": ["..."],
    "suggestions": ["..."],
    "confidence": "High - ...",
    "file_notes": ["..."]
  }
}
```

## 🏗️ Architecture

```
claude-review
├── claude_review/
│   ├── __init__.py         # Package metadata
│   ├── __main__.py         # python -m support
│   ├── cli.py              # CLI argument parsing & colored output
│   ├── github_client.py    # GitHub API integration
│   └── reviewer.py         # Claude API review engine
├── .github/workflows/
│   └── pr-review.yml       # GitHub Action workflow
├── sample-outputs/         # Example review outputs
├── claude-review           # Direct executable
├── pyproject.toml          # Package configuration
├── requirements.txt        # Dependencies
└── README.md               # This file
```

## 📄 License

MIT
