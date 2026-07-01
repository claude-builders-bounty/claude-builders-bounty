# Claude Code PR Review Agent

Automated PR review agent that analyzes diffs and posts structured Markdown comments.

## Setup (2 commands)

```bash
pip install claude-review-agent  # or copy agent/claude_review.py
gh auth login                     # Ensure GitHub CLI is authenticated
```

## Usage

### CLI Mode
```bash
# Review a GitHub PR
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Review a local diff file
python claude_review.py --diff path/to/diff.patch

# Save to file
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# JSON output
python claude_review.py --diff diff.patch --json
```

### GitHub Action
Add `.github/workflows/claude-review.yml` to your repo (included in this PR).

## Output Format

```markdown
## 🤖 Claude Code PR Review

**Confidence:** High

### 📋 Summary
This PR adds 45 lines across 3 files.

### ⚠️ Identified Risks
- 🟠 **[HIGH]** Potential credential handling

### 💡 Improvement Suggestions
- Consider using enumerate() for cleaner iteration

### 📊 Stats
- Files changed: 3
- Additions: 45
- Deletions: 12
```

## Risk Levels

| Level | Meaning |
|-------|---------|
| 🔴 CRITICAL | Code injection, security vulnerability |
| 🟠 HIGH | Destructive ops, credential handling |
| 🟡 MEDIUM | SQL ops, needs review |
| 🟢 LOW | Style issues, debug output |
