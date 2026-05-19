# Claude Code PR Review Agent

A Claude Code sub-agent that reviews GitHub pull requests and outputs structured Markdown feedback.

## Features

- **CLI Interface**: Review PRs via command line: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: Automated PR reviews via GitHub Actions workflow
- **Structured Output**: Provides consistent, formatted feedback including:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score (Low/Medium/High)
- **Real PR Testing**: Tested on actual GitHub PRs

## Installation

### Prerequisites

- Python 3.7+
- GitHub personal access token (with `repo` scope)
- Anthropic API key

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/claude-builders-bounty.git
   cd claude-builders-bounty
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file (or set environment variables):
   ```env
   GITHUB_TOKEN=your_github_personal_access_token
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

### Alternative: Use as GitHub Action

This repository includes a GitHub Action workflow that automatically reviews PRs. To use it:

1. Fork this repository
2. Add your Anthropic API key as a secret named `ANTHROPIC_API_KEY` in your fork's repository settings
3. The workflow will automatically run on PR events

## Usage

### CLI Usage

```bash
# Method 1: Provide tokens as arguments
python claude_review.py --pr https://github.com/owner/repo/pull/123 \
                        --github-token YOUR_GITHUB_TOKEN \
                        --anthropic-key YOUR_ANTHROPIC_KEY

# Method 2: Use environment variables (recommended for security)
export GITHUB_TOKEN=your_github_personal_access_token
export ANTHROPIC_API_KEY=your_anthropic_api_key
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

### Example Output

```
## Summary
This PR introduces changes to improve the authentication system by adding JWT token validation. The modifications are focused on security enhancements and appear to be well-implemented with proper error handling.

## Risks
- Potential performance impact on high-traffic endpoints due to additional validation
- Edge case with expired tokens not handled in logout flow
- No rate limiting on authentication attempts

## Improvements
- Add rate limiting to prevent brute force attacks
- Implement token refresh mechanism for better UX
- Add more comprehensive unit tests for edge cases
- Consider logging failed authentication attempts for monitoring

## Confidence
Medium
```

## Requirements

See `requirements.txt` for exact versions:
- anthropic
- python-dotenv (for local development)

## Testing

To test the agent with sample data:

```bash
# Run unit tests (when implemented)
python -m pytest tests/

# Or test with a real PR (replace with actual PR URL)
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

## How It Works

1. **Input**: Takes a GitHub PR URL
2. **Data Fetching**: Uses GitHub API to get PR details, changed files, and diff
3. **Analysis**: Sends the PR information to Claude API for analysis
4. **Output**: Returns structured Markdown feedback

## Configuration

You can customize the behavior by modifying:
- `claude_review.py`: Core logic and prompts
- `.github/workflows/pr-review.yml`: GitHub Action configuration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Claude Code](https://claude.com/claude-code)
- Powered by [Anthropic's Claude API](https://www.anthropic.com/api)
- Inspired by the Claude Builders Bounty program