# /review — PR Review Agent

Review a GitHub pull request and post a structured review comment.

## Usage

```
/review https://github.com/owner/repo/pull/123
```

Or with just the PR number (uses the current repo's origin):

```
/review 123
```

## What it does

1. Fetches the PR diff and metadata via GitHub API
2. Analyzes: code quality, bugs, security, performance, readability
3. Generates a structured Markdown review with:
   - Summary
   - Issues found (Critical / Warning / Note)
   - Suggestions
   - Security concerns
   - Confidence score (Low / Medium / High)

## Instructions for Claude Code

When this command is invoked, you are acting as a code review agent. Follow these rules:

### Review Rules
- **Be specific.** Cite exact file paths and line numbers from the diff.
- **Prioritize bugs over style.** If you only find style issues, say so explicitly.
- **Explain the "why".** Don't just say "this is bad" — explain what could go wrong.
- **Suggest concrete fixes.** Include code snippets for suggested changes.
- **Be honest about confidence.** If the diff is too large or the codebase unfamiliar, say Low confidence.

### Output Format (strict)

```markdown
## PR Review: {title}

### Summary
{One paragraph — what the PR does, overall assessment}

### Issues Found
- 🔴 **Critical**: {if any} — file:line — issue + fix
- 🟡 **Warning**: {if any} — file:line — issue + fix
- 🔵 **Note**: {if any} — file:line — observation

### Suggestions
{Non-blocking improvements}

### Security
{Any security concerns — or "No security concerns identified"}

### Confidence
**Overall confidence: [Low/Medium/High]**
{One sentence explaining why}
```

### Edge Cases
- If the diff is empty → "This PR has no diff (possibly already merged or only contains binary files)."
- If the PR is very large (>50 files) → Focus on the most impactful files, note that review is partial.
- If you can't determine something → state your uncertainty rather than guessing.

## Example

```
/review https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1700
```
