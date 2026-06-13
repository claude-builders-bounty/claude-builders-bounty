name: pr-review
description: >
  Review a GitHub Pull Request by fetching its diff via the GitHub API and
  producing a structured Markdown report with Overview, Good parts, Concerns,
  Suggestions, and a Confidence score. Integrates with `claude-review.py`.
instructions: |
  You can review GitHub Pull Requests using the `claude-review` tool.

  ## Commands

  ### `claude-review --pr <url>`

  Fetches and analyzes a GitHub PR, returning structured Markdown.

  **Parameters:**
  - `--pr` (required): Full GitHub PR URL — e.g. `https://github.com/owner/repo/pull/123`
  - `--token` (optional): GitHub token (defaults to `$GITHUB_TOKEN`)
  - `--format` (optional): `markdown` (default) or `json`

  **Example invocation:**
  ```
  python3 /path/to/pr-review-agent/claude-review.py --pr https://github.com/numpy/numpy/pull/31622
  ```

  **Example output structure:**
  - PR metadata (title, author, state, commits)
  - File change breakdown with diffs
  - ✅ Good Parts — positive observations
  - ⚠️ Concerns — potential issues detected
  - 💡 Suggestions — actionable recommendations
  - Confidence Score (Low / Medium / High)

  ## Static Analysis Checks

  The tool automatically detects:
  - Debug `print()` calls left in code
  - Bare `except:` clauses
  - `TODO`/`FIXME`/`HACK` comments
  - Use of `eval()`/`exec()`
  - Wildcard imports (`import *`)
  - Hardcoded secrets or API keys
  - Very large files (>300 lines changed)
  - Missing tests for code changes
  - Empty PR descriptions
  - Cross-language changes
  - Config/secret file modifications

  ## Workflow

  1. User provides a PR URL or asks you to review a PR
  2. You invoke `claude-review.py` with the URL
  3. The tool fetches the diff, runs static analysis, and returns structured Markdown
  4. You can then read the output and provide deeper reasoning or commentary
  5. If the user wants more detail, fetch specific file diffs with the GitHub API

  ## Environment

  Requires `GITHUB_TOKEN` environment variable with `repo` scope for private repositories
  (public repos work with fine-grained tokens too).
example: |
  User: "Review PR https://github.com/numpy/numpy/pull/31622"

  Agent:
  <invoke>
  <tool>bash</tool>
  <command>python3 pr-review-agent/claude-review.py --pr https://github.com/numpy/numpy/pull/31622</command>
  </invoke>

  (Outputs structured Markdown review directly to the conversation.)
