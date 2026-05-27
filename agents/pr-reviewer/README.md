# 🤖 Claude Code PR Review Agent

An autonomous Python agent that reviews GitHub Pull Requests and produces
**structured Markdown reviews** with a summary, risk analysis, improvement
suggestions, and a confidence score.

Works as a CLI tool, from stdin, or as a GitHub Action.

## Features

- **Pattern-based analysis** — detects hardcoded secrets, dangerous calls (exec/eval/os.system), SQL injections, CORS misconfigurations, TODO/FIXME markers, debug statements, skipped tests, and more
- **Heuristic scoring** — PR size, file complexity, test coverage signals, and documentation impact
- **Confidence scoring** — Low / Medium / High based on risk weight and PR complexity
- **Multiple input modes** — PR URL, local diff file, stdin pipe
- **Multiple output formats** — Markdown (default), JSON (with `--json`)
- **Zero external dependencies** — uses only Python 3.8+ stdlib
- **GitHub Action ready** — example workflow included

## Quick Start

```bash
# Clone the repo
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/agents/pr-reviewer

# Review a PR
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Save to a file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 -o review.md

# Review from a local diff
python3 claude-review.py --file /path/to/changes.patch

# Pipe from stdin
git diff main..feature | python3 claude-review.py

# Get raw JSON analysis
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --json > analysis.json
```

## Requirements

- Python 3.8 or later
- No external packages required

### Optional

- `GITHUB_TOKEN` environment variable — increases API rate limits for live PR fetching

## Output Sections

| Section | Content |
|---------|---------|
| **📋 Summary** | 2-3 sentence overview: files changed, additions/deletions, nature of changes |
| **📂 Files Changed** | File-level breakdown with +/- counts |
| **⚠️ Issues Found (🔴 High)** | Secrets, injections, dangerous calls, destructive ops |
| **⚠️ Issues Found (🟡 Medium)** | TODOs, debug prints, skipped tests, suppressed type errors |
| **💡 Improvement Suggestions** | Large-file refactoring, missing tests, missing docs |
| **✅ Confidence Score** | 🟢 High / 🟡 Medium / 🔴 Low with explanation |

## GitHub Action

To run automatically on every PR, add this workflow:

```yaml
# .github/workflows/pr-review.yml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/pr-reviewer/claude-review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            -o review-output.md
          cat review-output.md
```

## Sample Output

See [`sample-outputs/`](sample-outputs/) for example reviews on real open-source PRs.

## Running Tests

```bash
bash validate.sh
```

The validation script runs the agent against:
1. Its own source diff
2. A synthetic inline diff with known patterns
3. JSON output format verification
4. A real GitHub PR (requires `GITHUB_TOKEN`)

## File Structure

```
agents/pr-reviewer/
├── agent.md               # Sub-agent definition (goal, scope, workflow)
├── claude-review.py       # Main CLI tool
├── validate.sh            # Smoke-test script
├── test-pr-review.sh      # Demo script for real PRs
├── README.md              # This file
└── sample-outputs/        # Generated review outputs
    ├── self-review.md
    ├── stdin-review.md
    ├── analysis.json
    └── ...
```

## Confidence Score Logic

| Condition | Score |
|-----------|-------|
| No diff content | Low |
| Risk weight > 12 | Low |
| Risk weight > 4 | Medium |
| Total lines > 1500 | Medium |
| Otherwise | High |

Risk weight = (high-risk findings × 3) + (medium-risk findings)

## License

This is part of the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) repository.
