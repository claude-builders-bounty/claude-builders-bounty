# claude-review — AI PR Review with Claude

Get structured, senior-engineer-level PR reviews powered by Claude Sonnet 4.
Works as a **CLI tool** or a **GitHub Action**.

## CLI — Quick Start

### 1. Install

```bash
curl -L https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/claude-review -o claude-review && chmod +x claude-review
```

### 2. Set environment variables

```bash
export GITHUB_TOKEN="ghp_your_token"        # needs repo read access
export ANTHROPIC_API_KEY="sk-ant-..."      # from console.anthropic.com
```

### 3. Run

```bash
# By PR URL
./claude-review --pr https://github.com/owner/repo/pull/123

# By components
./claude-review --owner owner --repo repo --number 123

# From a local diff file
./claude-review --diff changes.patch

# JSON output (for scripting)
./claude-review --pr https://github.com/owner/repo/pull/123 --json

# Mock mode (testing without API key)
./claude-review --pr https://github.com/owner/repo/pull/123 --mock
```

## GitHub Action

### 1. Add secrets to your repo

In your repo Settings > Secrets and variables > Actions:
- `ANTHROPIC_API_KEY` — your Anthropic API key

(`GITHUB_TOKEN` is auto-provided by GitHub Actions)

### 2. Add workflow file

Copy `.github/workflows/claude-review.yml` and `.github/workflows/claude-review-action.py` from this repo into your repository.

### 3. Done

Every new PR (and every push to an open PR) gets an AI review comment automatically.

## Output Format

Every review contains:

| Section | Content |
|---------|---------|
| **Summary** | 2-3 sentences on what the PR does |
| **Identified Risks** | Concrete concerns, not generic advice |
| **Improvement Suggestions** | Actionable fixes and enhancements |
| **Confidence** | Low / Medium / High — how confident Claude is in its assessment |

### Example Output

```markdown
## PR Review — expressjs/express#7057

### Summary
This PR bumps the qs dependency to ^6.14.2 to address CVE-2026-2391,
a prototype pollution vulnerability. The change is minimal and targeted —
only the version constraint in package.json and package-lock.json are updated.

### Identified Risks
- Minor version bump could introduce subtle behavior changes in query string parsing;
  verify existing query-dependent routes still behave as expected
- If the project has pinned qs for a specific reason, this unpins it

### Improvement Suggestions
- Add a regression test that reproduces CVE-2026-2391 to confirm the fix works
- Consider adding a changelog entry noting the security update

### Confidence: High
```

## How It Works

1. Fetches the unified diff for the PR via GitHub API
2. Sends it to Claude Sonnet 4 with a system prompt instructing it to act as a senior engineer reviewer
3. Claude returns structured JSON (summary, risks, suggestions, confidence)
4. The tool formats it as Markdown and either prints it (CLI) or posts it as a PR comment (Action)

## Files

| File | Purpose |
|------|---------|
| `claude-review` | CLI tool (Python 3, zero dependencies beyond stdlib) |
| `.github/workflows/claude-review.yml` | GitHub Action workflow |
| `.github/workflows/claude-review-action.py` | GitHub Action script |
| `README-review.md` | This documentation |

## Requirements

- Python 3.7+ (stdlib only — no pip install needed)
- `GITHUB_TOKEN` with `repo` scope (for fetching PR diffs)
- `ANTHROPIC_API_KEY` (for calling Claude API)
