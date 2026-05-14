# PR Reviewer

Claude Code sub-agent that reviews a GitHub Pull Request and posts a structured Markdown review comment.

## Setup & Usage

### CLI

```bash
pip3 install -r /dev/null  # No dependencies — pure Python stdlib!
export GITHUB_TOKEN="ghp_..."
python3 pr-reviewer.py https://github.com/owner/repo/pull/123
```

### GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo — reviews are posted to every PR's `$GITHUB_STEP_SUMMARY`.

### Claude Code Integration

Add to `CLAUDE.md`:
```
Use `python3 pr-reviewer.py <PR_URL>` to review a pull request before merging.
```

## Output

```markdown
# 🔍 Pull Request Review

## 📋 Summary
This PR modifies 3 files with +45 / -12 lines of change involving `.ts`, `.tsx`.

## ⚠️ Risks Identified
- Debug code (console.log) detected — should be removed before merge

## 💡 Improvement Suggestions
- Good practice adding tests — ensure coverage is adequate

## ✅ Confidence Score
**🟢 High**
```

## Requirements

- Python 3.6+
- GitHub token (for API access; optional for local .patch files)
