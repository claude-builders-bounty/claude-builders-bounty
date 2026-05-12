# Claude PR Review Agent

An AI-powered pull request reviewer that uses Claude to generate structured, actionable code reviews. Available as both a CLI tool and a GitHub Action.

## Features

- Structured Markdown output with Summary, Risk Assessment, Suggestions, and Confidence score
- Detects real issues: security vulnerabilities, performance regressions, correctness bugs, compatibility risks
- References specific files and line numbers in suggestions
- Optionally posts reviews as PR comments
- Works on any public or accessible GitHub repository
- Handles large diffs with automatic truncation

## Prerequisites

### CLI Tool

- [GitHub CLI (`gh`)](https://cli.github.com/) -- authenticated with `gh auth login`
- [Claude Code CLI (`claude`)](https://docs.anthropic.com/en/docs/claude-code) -- installed and configured
- `jq` -- for JSON parsing (pre-installed on most systems)

### GitHub Action

- `ANTHROPIC_API_KEY` -- set as a repository secret (Settings > Secrets and variables > Actions)
- `GITHUB_TOKEN` -- automatically provided by GitHub Actions (no setup needed)

## CLI Usage

### Installation

```bash
# Clone the repository
git clone https://github.com/opire/claude-builders-bounty.git
cd claude-builders-bounty/bounty-4-agent

# The script is already executable, but just in case:
chmod +x claude-review.sh

# Option A: Symlink to your PATH
ln -s "$(pwd)/claude-review.sh" /usr/local/bin/claude-review

# Option B: Copy directly
cp claude-review.sh /usr/local/bin/claude-review
```

### Basic Usage

Review a PR and print the output to stdout:

```bash
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

Review a PR and post the review as a comment on the PR:

```bash
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --post-comment
```

Use a specific Claude model:

```bash
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --model opus
```

### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--pr <URL>` | GitHub PR URL (required) | -- |
| `--post-comment` | Post review as a PR comment | `false` |
| `--model <MODEL>` | Claude model to use | `sonnet` |
| `--help` | Show help message | -- |
| `--version` | Show version | -- |

## GitHub Action Usage

### Setup

1. Copy the workflow file to your repository:

```bash
mkdir -p .github/workflows
cp bounty-4-agent/.github/workflows/pr-review.yml .github/workflows/pr-review.yml
```

2. Add your Anthropic API key as a repository secret:
   - Go to your repository on GitHub
   - Navigate to **Settings > Secrets and variables > Actions**
   - Click **New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Value: your Anthropic API key from https://console.anthropic.com/

3. The action will automatically run on every new PR and on every push to an existing PR.

### Workflow Triggers

The workflow triggers on:

- `pull_request: opened` -- when a new PR is created
- `pull_request: synchronize` -- when new commits are pushed to a PR

The review is posted as a comment on the PR with a `<!-- claude-review-bot -->` HTML marker for identification.

### Customization

To restrict which PRs get reviewed, add path filters:

```yaml
on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'src/**'
      - '!*.md'
```

## Review Output Format

Every review follows this consistent structure:

```markdown
## PR Review: {title}

**PR**: #{number} | **Author**: {author} | **Branch**: `head` -> `base`
**Changes**: +X/-Y across N files

### Summary
2-3 sentence overview of the PR's purpose and approach.

### Risk Assessment
| Risk | Severity | Details |
|------|----------|---------|
| ... | Critical/High/Medium/Low | Specific explanation with file/line references |

### Suggestions
1. **Title** (`file:line`) -- Actionable improvement with explanation.

### What Looks Good
- Positive observations about code quality, patterns, etc.

### Confidence
**Low/Medium/High** -- Justification based on diff size, complexity, and context.
```

### Review Focus Areas

The review prompt instructs Claude to look for:

- **Security**: SQL injection, XSS, CSRF, auth bypasses, secrets in code, insecure defaults
- **Performance**: N+1 queries, unnecessary re-renders, missing indexes, unbounded loops, memory leaks
- **Correctness**: Off-by-one errors, null/undefined handling, race conditions, missing error handling
- **Compatibility**: Breaking API changes, migration issues, deprecated APIs
- **Code Quality**: Dead code, duplication, unclear naming, missing types
- **Testing**: Missing coverage for new logic, untested edge cases
- **Documentation**: Missing or outdated comments, API docs

## Sample Reviews

See the `sample-reviews/` directory for example outputs:

- [sample-review-1.md](sample-reviews/sample-review-1.md) -- Small PR adding a user search API endpoint (+142/-3, 4 files). Catches SQL injection, missing auth, unbounded pagination.
- [sample-review-2.md](sample-reviews/sample-review-2.md) -- Large PR refactoring authentication from custom JWT to NextAuth (+1,847/-923, 34 files). Catches hardcoded secret fallback, incomplete session invalidation, race conditions in cleanup jobs.

## How It Works

### CLI Flow

1. Parses the PR URL to extract `owner/repo` and PR number
2. Fetches PR metadata (title, body, files, stats) via `gh pr view --json`
3. Fetches the full diff via `gh pr diff`
4. Truncates large diffs (>8,000 lines) to stay within context limits
5. Sends the diff and metadata to Claude Code CLI with a structured review prompt
6. Outputs the Markdown review to stdout
7. Optionally posts the review as a PR comment via `gh pr comment`

### GitHub Action Flow

1. Triggers on `pull_request` events (opened, synchronize)
2. Fetches PR data using the GitHub CLI (authenticated via `GITHUB_TOKEN`)
3. Calls the Anthropic Messages API directly with `curl` (no Claude CLI dependency)
4. Uses Python for safe JSON escaping of the diff content
5. Posts the review as a PR comment via `gh pr comment`

## Architecture Decisions

- **CLI uses Claude Code CLI**: Leverages the full Claude Code experience with streaming output and local model selection.
- **GitHub Action uses Anthropic API directly**: Avoids requiring Claude CLI installation in CI. Uses `curl` with proper JSON escaping via Python for reliability with arbitrary diff content.
- **Safe GitHub Actions patterns**: All PR metadata is fetched via `gh` CLI and read from files, never interpolated from `${{ }}` expressions in `run:` blocks, preventing command injection from untrusted PR titles/bodies.
- **Diff truncation**: Large diffs are truncated (8K lines for CLI, 6K for Action) with a note to the reviewer, keeping API costs reasonable while covering most PRs fully.

## Limitations

- Very large PRs are truncated; some files may not be fully reviewed
- Binary file changes are not analyzed
- The review is based solely on the diff -- broader architectural context may be missed
- Confidence is calibrated but not guaranteed; always apply human judgment

## License

MIT
