
# PR Reviewer Agent

An automated code review agent for GitHub Pull Requests that analyzes code changes and provides structured feedback.

## Features

- Analyzes code diffs from GitHub PRs
- Provides structured Markdown feedback with:
  - Summary of changes
  - Critical issues
  - Code quality and style suggestions
  - Performance optimizations
  - Documentation improvements
  - Testing recommendations
- Integrates with GitHub Actions for automated reviews

## Installation

1. **Add the workflow file**:
   - Copy `.github/workflows/pr-reviewer-agent.yml` to your repository

2. **Add the review agent script**:
   - Copy the `agents/pr-reviewer/review_agent.py` file to your repository

3. **Set up secrets**:
   - Add `LLM_API_KEY` to your GitHub repository secrets (Settings > Secrets > Actions)
     - This should be an API key for your preferred LLM service (e.g., OpenAI)

## Configuration

The workflow is triggered automatically on:
- PR opened
- PR synchronized (new commits pushed)
- PR reopened

## Customization

You can customize the review behavior by modifying the `review_agent.py` script:

1. **System Prompt**: Edit the `system_prompt` variable to change the review criteria
2. **LLM Model**: Change the `LLM_MODEL` variable to use a different model
3. **API Endpoint**: Update `LLM_API_URL` if using a different LLM provider

## Example Output

The agent generates a Markdown review with sections like:

```markdown
## Summary of Changes
- Added new user authentication endpoint
- Updated database schema for user profiles

## Critical Issues
- **File**: `api/auth.py`, Line 42
  - **Issue**: Missing input validation for email parameter
  - **Suggestion**: Add email format validation using regex

## Code Quality & Style
- **File**: `models/user.py`, Line 15
  - **Issue**: Inconsistent naming convention for class method
  - **Suggestion**: Rename `getUserById` to `get_user_by_id` to follow Python naming conventions
```

## Requirements

- Python 3.10+
- GitHub repository with Actions enabled
- LLM API key (e.g., OpenAI API key)

## Troubleshooting

1. **Workflow not triggering**:
   - Ensure the workflow file is in `.github/workflows/`
   - Check that the workflow is enabled in your repository settings

2. **Review not posted**:
   - Verify the `GITHUB_TOKEN` has write permissions for PR comments
   - Check the Actions logs for error messages

3. **API errors**:
   - Ensure the `LLM_API_KEY` secret is correctly set
   - Verify the LLM API endpoint is correct in the script
