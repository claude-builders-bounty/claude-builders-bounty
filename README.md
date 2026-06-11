# PR Reviewer Agent

Structured Markdown output PR reviewer for GitHub.

## Installation

```bash
pip install -r requirements.txt
python pr-reviewer.py < pr-data.json
```

## Usage

```bash
curl https://api.github.com/repos/owner/repo/pulls/123 \
  | python pr-reviewer.py
```

## Output

Structured JSON with:
- Code quality scores
- Security analysis
- Performance recommendations
- Test coverage assessment

## Features

- Modular category-based review
- Configurable scoring system
- Structured markdown output
- Easy integration with CI/CD
