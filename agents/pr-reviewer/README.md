# Claude Code PR Reviewer Agent

A CLI tool and GitHub Action that uses Claude Code to review pull requests and produce structured Markdown output with risk analysis, improvement suggestions, and confidence scoring.

**Bounty #4** -- claude-builders-bounty

---

## Features

- Review any public GitHub PR from the command line
- Structured Markdown output: summary, risks, suggestions, file notes, confidence score
- GitHub Action workflow for automatic reviews on PR open/sync
- Configurable prompt template
- Handles large diffs with automatic truncation (3000 line limit)
- Verbose mode for debugging

---

## Requirements

- [GitHub CLI (`gh`)](https://cli.github.com/) -- authenticated with `gh auth login`
- [Claude Code CLI (`claude`)](https://docs.anthropic.com/en/docs/claude-code) -- installed and configured
- Bash 4+

---

## Setup

### CLI Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
   cd claude-builders-bounty
   ```

2. Make the script executable:
   ```bash
   chmod +x agents/pr-reviewer/claude-review.sh
   ```

3. (Optional) Add to PATH:
   ```bash
   ln -s "$(pwd)/agents/pr-reviewer/claude-review.sh" /usr/local/bin/claude-review
   ```

4. Run a review:
   ```bash
   ./agents/pr-reviewer/claude-review.sh --pr https://github.com/owner/repo/pull/123
   ```

### CLI Options

| Option | Description |
|--------|-------------|
| `--pr <url>` | GitHub PR URL (required) |
| `--output <file>` | Write review to a file instead of stdout |
| `--verbose` | Show progress messages on stderr |
| `--help` | Show usage information |

### Examples

```bash
# Review a PR, print to stdout
./agents/pr-reviewer/claude-review.sh --pr https://github.com/vercel/next.js/pull/12345

# Save review to file
./agents/pr-reviewer/claude-review.sh --pr https://github.com/owner/repo/pull/42 --output review.md

# Verbose mode (shows progress on stderr)
./agents/pr-reviewer/claude-review.sh --pr https://github.com/owner/repo/pull/42 --verbose
```

---

## GitHub Action

The included workflow file (`pr-review.yml`) automatically reviews PRs when they are opened or updated.

### Setup

1. Copy the workflow file into your repository's GitHub Actions directory:
   ```bash
   mkdir -p .github/workflows
   cp agents/pr-reviewer/pr-review.yml .github/workflows/pr-review.yml
   ```

2. Add an `ANTHROPIC_API_KEY` secret to your repository:
   - Go to Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `ANTHROPIC_API_KEY`
   - Value: your Anthropic API key

3. The workflow uses `GITHUB_TOKEN` automatically for PR access and commenting.

4. Once configured, every new PR and push to an existing PR triggers an automated review comment.

### How It Works

1. The Action checks out the repository
2. Installs the Claude Code CLI
3. Fetches the PR diff and metadata using `gh`
4. Builds the review prompt from `review-prompt.md`
5. Sends the prompt to Claude via `claude --print`
6. Posts the structured review as a PR comment

---

## Output Format

Every review follows this structure:

```
# PR Review: [title]

**PR**: [url]
**Author**: [author]
**Reviewed by**: claude-review (Claude Code PR Reviewer Agent)
**Date**: [date]

---

## Summary
[2-3 sentence overview]

## Identified Risks
- [Risk with severity]

## Improvement Suggestions
- [Actionable suggestion with file/line reference]

## File-by-File Notes
| File | Status | Notes |
|------|--------|-------|
| ... | OK / Needs Changes / Critical | ... |

## Confidence Score
**[Low / Medium / High]**
[Explanation]
```

---

## Customizing the Prompt

Edit `review-prompt.md` to change what Claude focuses on. The template uses `{{variable}}` placeholders:

| Variable | Content |
|----------|---------|
| `{{PR_TITLE}}` | Pull request title |
| `{{PR_AUTHOR}}` | PR author's GitHub username |
| `{{PR_URL}}` | Full PR URL |
| `{{PR_BODY}}` | PR description body |
| `{{PR_DIFF}}` | The full diff (truncated at 3000 lines) |
| `{{DATE}}` | Today's date (YYYY-MM-DD) |

---

## Example Outputs

See the `examples/` directory for sample review outputs:

- `examples/example-review-1.md` -- Review of a dependency update PR
- `examples/example-review-2.md` -- Review of a feature PR with security considerations

---

## License

MIT
