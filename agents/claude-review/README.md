# Claude Review Agent

A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown comments.

## Features

- **CLI Tool**: Review any GitHub PR from the command line
- **GitHub Action**: Automatically review PRs in your CI/CD pipeline
- **Structured Output**: Get summary, risks, suggestions, and confidence score
- **Flexible Formats**: Full or compact review output

## Installation

### From Source

```bash
git clone https://github.com/jpalafox-12/claude-review.git
cd claude-review
pip install -e .
```

### Using pip

```bash
pip install claude-review
```

## Usage

### CLI

```bash
# Basic usage
claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Compact format
claude-review --pr https://github.com/owner/repo/pull/123 --format compact

# Post as GitHub comment
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

### Python API

```python
from claude_review import PRReviewer, format_review

# Initialize reviewer
reviewer = PRReviewer()

# Fetch PR data
pr_data = reviewer.fetch_pr_data("https://github.com/owner/repo/pull/123")

# Review PR
result = reviewer.review(pr_data)

# Format output
review = format_review(pr_data, result)
print(review)
```

### GitHub Action

Add this to your `.github/workflows/pr-review.yml`:

```yaml
name: Claude Review Agent

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Claude Review Agent
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python -m claude_review.cli --pr ${{ github.event.pull_request.html_url }}
```

## Output Format

### Full Format

```markdown
## Summary
This PR adds JWT authentication with token refresh...

## Identified Risks
- ⚠️ Token expiration not handled
- ⚠️ No rate limiting on login

## Improvement Suggestions
- 💡 Add token refresh mechanism
- 💡 Implement rate limiting

## Confidence Score
**High** 🟢
```

### Compact Format

```markdown
## 🤖 Claude Review Agent

**High Confidence** 🟢

### Summary
This PR adds JWT authentication...

### Risks
- Token expiration not handled

### Suggestions
- Add token refresh mechanism
```

## Development

### Setup

```bash
# Clone the repo
git clone https://github.com/jpalafox-12/claude-review.git
cd claude-review

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Install dev dependencies
pip install black flake8 mypy

# Format code
black .

# Lint code
flake8 .

# Type check
mypy .
```

## Requirements

- Python 3.8+
- GitHub CLI (`gh`) installed and authenticated
- GitHub token (for API access)

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and questions, please open an issue on GitHub.
