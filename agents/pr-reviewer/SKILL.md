# PR Reviewer Skill

Automated GitHub Pull Request code review agent. Analyzes diffs for security, performance, and code quality issues, then posts a structured review comment.

## Quick Start

```bash
# 1. Set your GitHub token
export GITHUB_TOKEN="ghp_..."

# 2. Review a PR (prints to stdout)
python pr-reviewer.py --repo owner/repo --pr 123

# 3. Post the review as a PR comment
python pr-reviewer.py --repo owner/repo --pr 123 --post
```

## Tool Usage

When the user asks to review a PR, follow these steps:

1. **Identify the repo and PR number** from the user's request. They may provide:
   - A GitHub URL: `https://github.com/owner/repo/pull/123`
   - Explicit values: "review PR #123 in owner/repo"

2. **Run the reviewer** using the Python CLI tool:

   ```bash
   # Dry run — show review without posting
   python /path/to/pr-reviewer.py --repo owner/repo --pr 123

   # Post the review as a comment
   python /path/to/pr-reviewer.py --repo owner/repo --pr 123 --post
   ```

3. **Authentication**: The tool needs a GitHub token. Check for `GITHUB_TOKEN` or `GH_TOKEN` env vars. If not set, ask the user to provide one.

4. **Review output** includes:
   - **Summary** — PR title, author, files changed, line counts
   - **Quality Score** — 1–10 with visual bar
   - **Security Concerns** — hardcoded secrets, injection risks, unsafe patterns
   - **Performance Suggestions** — loops, N+1 queries, async opportunities
   - **Line-by-Line Feedback** — grouped by file with severity and line number
   - **Improvements** — actionable next steps

## Options

| Flag | Description |
|------|-------------|
| `--repo` | GitHub repo in `owner/repo` format (required) |
| `--pr` | Pull request number (required) |
| `--post` | Post the review as a PR comment (requires auth) |
| `--output FILE` | Write review markdown to a file |
| `--json` | Output raw structured data as JSON |
| `--token TOKEN` | GitHub token (alternative to env var) |

## Example Workflow

User: "Can you review https://github.com/acme/app/pull/47?"

```
1. Extract: repo = "acme/app", pr = 47
2. Run: python pr-reviewer.py --repo acme/app --pr 47
3. Show the user the review output
4. Ask: "Would you like me to post this as a comment on the PR?"
5. If yes: python pr-reviewer.py --repo acme/app --pr 47 --post
```

## Output Format

The review is formatted as GitHub-flavoured Markdown:

```markdown
## 🤖 Automated PR Review

**PR #47**: Fix authentication bypass
**Author**: octocat
**Base → Head**: `main` ← `fix/auth-bypass`

**3 file(s) changed**: +87 / -12 lines

### Code Quality: 8/10  `████████░░`

### 🔒 Security Concerns
- ⚠️ Hardcoded secret or credential detected.

### ⚡ Performance Suggestions
- ✅ No performance issues detected.

### 📝 Line-by-Line Feedback

**`src/auth.py`**

| Line | Severity | Comment |
|------|----------|---------|
| L42  | 🔴 error | Hardcoded secret or credential detected. |
| L88  | 💡 suggestion | Debug `print()` left in code — use `logging`. |

### ✨ Suggested Improvements
1. Add or update tests to cover the changed logic.
2. Run `ruff check` to catch style/lint issues.
3. Ensure CI passes before requesting review.
```
