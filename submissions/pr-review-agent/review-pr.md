---
name: review-pr
description: Review a GitHub PR with structured feedback — check code quality, bugs, security, and style
args: PR number or URL
---

# /review-pr

Review a pull request and provide structured feedback.

## Input

The user will provide a PR number or GitHub URL. Parse the PR number from the input.

## Steps

1. Get the PR diff using: `gh pr diff <number>`
2. Get the PR description using: `gh pr view <number>`
3. Get the list of changed files: `gh pr diff <number> --name-only`
4. For each changed file, analyze:
   - **Bugs**: Logic errors, off-by-one, null/undefined handling, race conditions
   - **Security**: SQL injection, XSS, command injection, hardcoded secrets, unsafe deserialization
   - **Performance**: N+1 queries, unnecessary re-renders, missing indexes, large bundle imports
   - **Style**: Naming consistency, dead code, overly complex logic, missing error handling
   - **Testing**: Are new features tested? Are edge cases covered?

5. Output a structured review in this format:

```
## PR Review: #<number> — <title>

### Summary
<1-2 sentence summary of what the PR does>

### Issues Found

#### 🐛 Bugs
- [file:line] Description of bug

#### 🔒 Security  
- [file:line] Description of security concern

#### ⚡ Performance
- [file:line] Description of performance issue

#### 🎨 Style
- [file:line] Description of style improvement

### Verdict
- [ ] ✅ Approve — looks good
- [ ] 🔄 Request changes — issues found above
- [ ] ❓ Needs discussion — architectural questions

### Suggestions
<Optional positive suggestions or alternative approaches>
```

6. If there are no issues in a category, omit that section.
7. Be specific — reference exact file paths and line numbers.
8. Be constructive — explain WHY something is an issue and suggest a fix.
