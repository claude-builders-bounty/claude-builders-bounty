# claude-review

A zero-dependency CLI tool that reviews GitHub pull requests and outputs structured Markdown reports.

No API keys, no cloud services, no package installs. Just `gh` + `jq` + standard Unix tools.

## What it does

Point it at any public (or accessible) GitHub PR and it will:

1. Fetch the PR metadata and diff via `gh`
2. Scan for risky patterns: hardcoded secrets, debug statements, empty catch blocks, missing tests, oversized PRs
3. Output a clean Markdown report with summary, risks, suggestions, stats, and a confidence score

## Requirements

- [GitHub CLI (`gh`)](https://cli.github.com/) — authenticated (`gh auth login`)
- `jq` — usually pre-installed on macOS, available via `apt`/`brew` everywhere else
- Bash 4+

## Install

```bash
# Clone and symlink (or just copy the script somewhere on your PATH)
git clone https://github.com/wocaoac-cpu/claude-builders-bounty.git
ln -s "$(pwd)/claude-builders-bounty/agents/claude-review/claude-review" /usr/local/bin/claude-review
```

Or just download the single file:

```bash
curl -sL https://raw.githubusercontent.com/wocaoac-cpu/claude-builders-bounty/feat/claude-review-agent/agents/claude-review/claude-review -o /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

## Usage

```bash
# Full PR URL
claude-review --pr https://github.com/facebook/react/pull/32650

# Short form
claude-review --pr facebook/react#32650

# Just a number (infers repo from current git directory)
claude-review --pr 42
```

## What it checks

| Category | Patterns |
|----------|----------|
| **Security** | Hardcoded API keys/secrets/tokens, private key material, .env files in diff |
| **Debug leftovers** | `console.log`, `debugger`, `pdb.set_trace`, `binding.pry` |
| **Code quality** | Empty catch blocks, functions >50 lines, lines >120 chars |
| **Maintenance** | TODO/FIXME/HACK comments |
| **Coverage** | Source files changed without corresponding test changes |
| **Scope** | PR size (warns at 500+ lines, flags at 1000+) |
| **Dependencies** | Changes to package.json, requirements.txt, go.mod, etc. |

## Output format

The report includes:

- **Summary** — what the PR does, who authored it, which files are involved
- **File Changes** — per-file addition/deletion counts
- **Risk Assessment** — anything that needs attention before merge
- **Suggestions** — non-blocking improvements worth considering
- **Stats** — key metrics at a glance
- **Confidence Score** — High / Medium / Low overall assessment

## Example outputs

Two real-world PR reviews are included in [`examples/`](./examples/):

### 1. [facebook/react#32650](./examples/react-32650.md) — CI workflow cleanup

A small, well-scoped PR that refactors yarn commands in GitHub Actions. No issues detected, confidence: **High**.

### 2. [nodejs/node#57846](./examples/node-57846.md) — C FFI entrypoint for libnode

Adds 4 lines to `node.cc` but ships with zero tests. The tool flags the missing test coverage and drops confidence to **Medium**.

## GitHub Action

You can also run this as a GitHub Action. Create `.github/workflows/pr-review.yml`:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: sudo apt-get install -y jq

      - name: Run claude-review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sL https://raw.githubusercontent.com/wocaoac-cpu/claude-builders-bounty/main/agents/claude-review/claude-review -o /tmp/claude-review
          chmod +x /tmp/claude-review
          REVIEW=$(/tmp/claude-review --pr "${{ github.event.pull_request.html_url }}")
          gh pr comment "${{ github.event.pull_request.number }}" --body "$REVIEW"
```

## How it works

No magic. The script:

1. Parses the PR reference (URL, `owner/repo#num`, or bare number)
2. Calls `gh pr view` for metadata and `gh pr diff` for the actual diff
3. Runs a series of `grep`/`awk` pattern matches against the added lines
4. Tallies a risk score based on weighted signals
5. Renders the results as Markdown

The entire thing is a single bash script under 350 lines. Read it — it's straightforward.

## License

MIT
