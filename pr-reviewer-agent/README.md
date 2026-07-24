# Claude Code PR Reviewer Agent

A lightweight CLI tool for reviewing GitHub Pull Requests. Uses `gh` CLI to fetch PR diffs and performs heuristic analysis for common code risks and improvements.

## Features

- Fetch PR diffs via `gh` CLI (no GitHub token required)
- Heuristic analysis for security risks, code quality, and best practices
- Structured Markdown output with summary, risks, suggestions, and confidence score
- Simple, dependency-light implementation (Python 3.8+)

## Installation

1. Ensure you have Python 3.8 or later installed
2. Ensure `gh` CLI is installed and authenticated (`gh auth login`)
3. Clone this repository:
   ```bash
   git clone <repository-url>
   cd pr-reviewer-agent
   ```

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

### Example

```bash
python claude_review.py --pr https://github.com/octocat/Hello-World/pull/1
```

## Output Format

The tool outputs structured Markdown with:

- **Summary**: Brief overview of changes and findings
- **Risks**: Potential security vulnerabilities and code issues
- **Improvement Suggestions**: Code quality and best practice recommendations
- **Confidence**: Low/Medium/High based on risk assessment

## How It Works

1. Parses the PR URL to extract owner/repo and PR number
2. Uses `gh pr diff` to fetch the actual code changes
3. Applies heuristic analysis patterns to identify:
   - Hardcoded credentials (passwords, API keys, tokens)
   - SQL injection vulnerabilities
   - XSS vulnerabilities
   - Unsafe function usage (eval, innerHTML)
   - Code quality issues (empty catch blocks, TODOs)
4. Generates structured Markdown output

## Limitations

- Heuristic analysis only - may produce false positives/negatives
- Does not understand code semantics or context
- Requires `gh` CLI to be installed and authenticated
- Works with public repos or repos you have access to

## Contributing

Contributions welcome! Areas for improvement:
- Add more sophisticated analysis patterns
- Support for specific languages/frameworks
- Integration with AI models for deeper analysis
- Output formats beyond Markdown

## License

MIT License - see LICENSE file for details.