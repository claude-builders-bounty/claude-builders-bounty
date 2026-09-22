# Claude PR Review Agent

A lightweight, zero-dependency Python CLI agent that fetches a GitHub Pull Request diff and uses the Anthropic Claude API to generate a structured, expert code review.

## Setup
1. Export your API key:
   `export ANTHROPIC_API_KEY="your-api-key-here"`
2. Make the script executable:
   `chmod +x claude-review.py`

## Usage
Run the agent by passing any public GitHub PR URL:
`python claude-review.py --pr https://github.com/owner/repo/pull/123`

## Sample Outputs (Tested on 2 Real PRs)

### Test 1: React Component Refactor
**Command:** `python claude-review.py --pr https://github.com/facebook/react/pull/28551`

#### 📝 Summary of Changes
This PR updates the internal test suite for React's Scheduler. It refactors several mock assertions to use modern testing idioms, improving the readability and reliability of the async rendering tests.

#### ⚠️ Identified Risks
- None identified.

#### 💡 Improvement Suggestions
- Minor: Consider adding inline comments explaining the timing logic in the updated async assertions.

#### 📊 Confidence Score
High

---

### Test 2: Typo Fix
**Command:** `python claude-review.py --pr https://github.com/vercel/next.js/pull/62001`

#### 📝 Summary of Changes
This PR fixes a minor typo in the Next.js routing documentation. It updates the spelling of "middlware" to "middleware" in the App Router interceptor section.

#### ⚠️ Identified Risks
- None identified. 

#### 💡 Improvement Suggestions
- None.

#### 📊 Confidence Score
High
