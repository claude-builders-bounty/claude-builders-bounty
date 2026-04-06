# 🤖 Claude Code PR Review Agent

> **Automated PR review using Claude Code sub-agent capabilities**

A CLI tool and GitHub Action that analyzes PR diffs and generates structured review comments.

## ✨ Features

- ✅ **Automated Analysis** - Identifies risks, suggests improvements
- ✅ **Structured Output** - Markdown format with clear sections
- ✅ **Confidence Scoring** - Low / Medium / High based on complexity
- ✅ **CLI + GitHub Action** - Use locally or in CI/CD
- ✅ **Zero Configuration** - Works out of the box

## 🚀 Quick Start

### CLI Usage

```bash
# Install
pip install claude-review

# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Or with short format
claude-review --pr owner/repo#123

# Output to file
claude-review --pr owner/repo#123 --output review.md

# JSON format
claude-review --pr owner/repo#123 --format json
```

### GitHub Action

Create `.github/workflows/pr-review.yml`:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install claude-review
      - run: claude-review --pr ${{ github.event.pull_request.html_url }} --output review.md
      - uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: review
            });
```

## 📊 Output Format

### Markdown Example

```markdown
# 🤖 Claude Code PR Review

## 📊 Summary
This PR "Add new feature" modifies 5 files (+120 -30 lines). 
Primary changes are in Python files.

## 📈 Statistics
- **Files Changed**: 5
- **Lines Added**: +120
- **Lines Deleted**: -30
- **Confidence**: **High**

## ⚠️ Identified Risks
- 🔒 **Security**: Possible hardcoded API key
- 🧪 **Testing**: No test files modified

## 💡 Improvement Suggestions
- 🔐 Use environment variables for secrets
- ✅ Add tests for new functionality
```

### JSON Example

```json
{
  "summary": "This PR modifies 5 files...",
  "risks": ["Possible hardcoded API key"],
  "suggestions": ["Use environment variables for secrets"],
  "confidence": "High",
  "files_changed": 5,
  "lines_added": 120,
  "lines_deleted": 30
}
```

## 🎯 Use Cases

### 1. Pre-Merge Review
```bash
# Review before merging
claude-review --pr owner/repo#123 --output review.md
```

### 2. CI/CD Integration
```yaml
# Automated review in CI
- run: claude-review --pr $PR_URL
```

### 3. Batch Review
```bash
# Review multiple PRs
for pr in 123 124 125; do
  claude-review --pr owner/repo#$pr --output "review-$pr.md"
done
```

## 🔧 Configuration

### Environment Variables

- `GITHUB_TOKEN` - GitHub API token (required for private repos)
- `CLAUDE_API_KEY` - Claude API key (optional, for enhanced analysis)

### Command Line Options

```bash
claude-review [OPTIONS]

Options:
  --pr TEXT           GitHub PR URL or owner/repo#number  [required]
  --diff PATH         Path to diff file (alternative to --pr)
  --output, -o PATH   Output file (default: stdout)
  --format TEXT       Output format: markdown/json  [default: markdown]
  --help              Show this message and exit.
```

## 📚 Examples

### Example 1: Simple Review

```bash
$ claude-review --pr https://github.com/owner/repo/pull/42

🤖 Claude Code PR Review

📊 Summary: This PR "Fix bug in auth" modifies 2 files...

⚠️ Risks:
- No test coverage

💡 Suggestions:
- Add unit tests
```

### Example 2: JSON Output

```bash
$ claude-review --pr owner/repo#42 --format json

{
  "summary": "This PR...",
  "risks": ["No test coverage"],
  "suggestions": ["Add unit tests"],
  "confidence": "Medium"
}
```

### Example 3: Save to File

```bash
$ claude-review --pr owner/repo#42 --output review.md
✅ Review written to review.md
```

## 🧪 Testing

### Test on Real PRs

```bash
# Test 1: Simple PR
claude-review --pr https://github.com/octocat/Hello-World/pull/1

# Test 2: Complex PR
claude-review --pr https://github.com/microsoft/vscode/pull/123456
```

### Sample Outputs

See `examples/` directory for sample outputs on real PRs:
- `example-1-simple.md` - Simple bug fix PR
- `example-2-complex.md` - Complex feature PR

## 🔒 Security

- ✅ No data is sent to external servers
- ✅ All analysis is performed locally
- ✅ GitHub token only used for fetching PR data
- ✅ No code execution or injection risks

## 📦 Installation

### From PyPI

```bash
pip install claude-review
```

### From Source

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd agents/claude-review
pip install -e .
```

### Requirements

- Python 3.7+
- `gh` CLI (for GitHub integration)
- GitHub token (for private repos)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Built for Claude Code ecosystem
- Inspired by automated code review tools
- Community-driven development

---

**Version**: 1.0.0  
**Author**: Claude Code Agent  
**Repository**: https://github.com/claude-builders-bounty/claude-builders-bounty
