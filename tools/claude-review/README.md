# Claude PR Review Agent

Automated code review for GitHub pull requests using Claude AI.

## Installation

### Prerequisites
- GitHub CLI (`gh`) installed and authenticated
- Python 3.8+
- Anthropic API key (optional - works without but gives better results with it)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Make executable
chmod +x claude-review

# Set API key (optional but recommended)
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

### Basic Review

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

### Save to File

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

## How It Works

1. **Fetches PR Details** - Uses GitHub CLI to get PR metadata and diff
2. **Analyzes with Claude** - Sends diff to Claude API for structured analysis
3. **Generates Review** - Returns formatted Markdown with:
   - Summary of changes
   - Identified risks
   - Improvement suggestions
   - Confidence score

## Output Format

```markdown
# Code Review: Add user authentication

**Repository:** owner/repo
**PR:** #123

## Summary

This PR implements user authentication using JWT tokens.

## Identified Risks

- ⚠️ Password hashing uses default bcrypt rounds
- 🔒 JWT secret validation missing

## Improvement Suggestions

- Add rate limiting middleware
- Validate JWT secret on startup

## Confidence Score

**High** - Implementation follows best practices overall.
```

## Examples

See `examples/` directory for real PR reviews.

## License

MIT
