# Sample Output — claude-review

## Test 1: PR #4767 (changelog generator)

**PR:** feat: add changelog generator script and skill
**Changes:** +4 files, +380 lines

### 🤖 AI Review

### Summary
This PR adds a changelog generator script that parses git history and produces a structured CHANGELOG.md. The implementation is clean with good separation of concerns.

### 🔴 Identified Risks
- No input validation on git tag format
- Large repos may cause memory issues with full commit history

### 💡 Improvement Suggestions
- Add `--limit` option for large repos
- Consider caching parsed git log output

### Confidence Score: Medium

---

## Test 2: PR #4818 (CLAUDE.md template)

**PR:** feat: add CLAUDE.md template for Next.js + SQLite SaaS (bounty #2)
**Changes:** +1 file, +439 lines

### 🤖 AI Review

### Summary
This PR adds a comprehensive CLAUDE.md template for Next.js + SQLite SaaS projects. Well-structured with clear conventions and best practices.

### 🔴 Identified Risks
- Template assumes SQLite — may confuse teams using other databases
- Some rules may conflict with existing project conventions

### 💡 Improvement Suggestions
- Add a "Quick Start" section at the top
- Include a checklist for teams adopting the template

### Confidence Score: High
