# Claude PR Review Agent

A CLI tool that uses Anthropic's `claude` CLI agent to automatically review GitHub Pull Requests and generate structured Markdown feedback.

## Requirements
- Python 3.8+
- `requests` library (`pip install requests`)
- Anthropic Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- (Optional) `GITHUB_TOKEN` environment variable for private repos or to avoid rate limits.

## Installation

1. Clone or download this directory.
2. Make the script executable:
```bash
chmod +x claude-review.py
```

## Usage

Run the script by passing a GitHub PR URL via the `--pr` flag:

```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123
```

The script will fetch the raw diff from GitHub, pipe it safely into the local `claude` agent context, and output a structured review containing:
- Summary of Changes
- Identified Risks
- Improvement Suggestions
- Confidence Score (Low / Medium / High)

## Sample Output

```markdown
### Summary of Changes
This PR introduces a new `.github/FUNDING.yml` file to enable the native GitHub Sponsors button on the repository. It also adds a detailed `donations.md` research document comparing various open-source funding platforms like Polar.sh and Open Collective.

### Identified Risks
- None identified. The changes are strictly markdown documentation and YAML configuration.

### Improvement Suggestions
- Looks good as is.

### Confidence Score
High
```
