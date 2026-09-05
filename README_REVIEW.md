# Claude Code PR Reviewer CLI

A sub-agent for Claude Code that automatically reviews a GitHub Pull Request using the Anthropic API.

## Setup
1. Ensure you have Python 3 installed.
2. Export your Anthropic API Key: `export ANTHROPIC_API_KEY="sk-ant-..."`
3. (Optional) Export a GitHub token if testing private repos: `export GITHUB_TOKEN="..."`
4. Make the script executable: `chmod +x claude-review.py`

## Usage
```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output Format
The agent will output a structured Markdown response containing:
1. Summary of changes (2-3 sentences)
2. Identified risks
3. Improvement suggestions
4. Confidence score
