# Claude PR Review Agent

A Python CLI agent that leverages the GitHub API and Anthropic's Claude 3.0 API to automatically review Pull Requests and generate structured Markdown feedback.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install requests
   ```

2. **Set Environment Variables:**
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
   ```

3. **Make Executable:**
   ```bash
   chmod +x claude-review.py
   ```

## Usage

Run the script by passing the full URL of the GitHub PR you want reviewed:
```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output Format
The agent will output a structured Markdown response containing:
1. **Summary of Changes**
2. **Identified Risks**
3. **Improvement Suggestions**
4. **Confidence Score**