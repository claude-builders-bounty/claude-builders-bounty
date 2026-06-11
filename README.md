# Claude Code PR Reviewer Agent

An automated agent that takes a GitHub PR diff and generates a structured, high-quality Markdown review.

## 🚀 Installation

1. Ensure you have the `gh` CLI installed and authenticated.
2. Copy `claude-review` to your local bin:
   ```bash
   chmod +x claude-review
   sudo mv claude-review /usr/local/bin/claude-review
   ```

## 🛠 Usage

Run the agent by providing the PR URL or number:

```bash
# Using PR URL
claude-review --pr https://github.com/owner/repo/pull/123

# Using PR number (requires --repo)
claude-review --pr 123 --repo owner/repo
```

## 📊 Review Structure

The agent provides:
1. **Summary of Changes**: A concise 2-3 sentence overview.
2. **Identified Risks**: A bulleted list of potential bugs or security flaws.
3. **Improvement Suggestions**: Actionable tips to improve code quality.
4. **Confidence Score**: An assessment of the review's accuracy (Low/Medium/High).

## 🧪 Sample Test Output

**PR**: `https://github.com/nkar123412-hub/claude-builders-bounty/pull/2685`
**Output**:
## 📝 Summary of Changes
Implemented a security hook to block destructive bash commands (`rm -rf`, `DROP TABLE`, etc.). Added a logging system and README.

## ⚠️ Identified Risks
- Regex for `DELETE FROM` might be too broad and block valid complex queries.
- Log file permissions might cause errors in restricted environments.

## 💡 Improvement Suggestions
- Use a more robust SQL parser instead of regex for complex queries.
- Add a whitelist for trusted directories.

## 🎯 Confidence Score: High
