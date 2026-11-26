# claude-review

A Claude Code sub-agent (CLI + GitHub Action) that reviews a pull request and posts a structured Markdown review.

## Install

```bash
git clone https://github.com/anlogrian-rgb/claude-review.git && cd claude-review && chmod +x claude_review.py
```

Requires the `gh` CLI (already authenticated) and Python 3.8+.

## Usage (CLI)

```bash
./claude_review.py --pr https://github.com/owner/repo/pull/123
```

Options:
- `--json` — emit JSON instead of Markdown
- `--out FILE` — write the review to a file

## Usage (GitHub Action)

Copy `.github/workflows/claude-review.yml` into your repo. It runs on `pull_request`
and posts the review as a PR comment using the built-in `GITHUB_TOKEN`.

## Output structure

```markdown
## 🤖 Claude Code Review

> **PR**: <title>
> **URL**: <url>
> **State**: OPEN

### 📋 Summary
2–3 sentence summary of the change (files, +/-, touched paths).

### ⚠️ Identified Risks
- Hardcoded secret / destructive SQL / shell=True / eval / verify=False …

### 💡 Improvement Suggestions
- Missing description, oversized diff, no tests, sensitive files …

### ✅ Confidence: Low | Medium | High
```

## Sample outputs (real PRs)

- `sample-outputs/pr-5307.md` — clean skill PR → Confidence **High**
- `sample-outputs/pr-5308.md` — PR containing destructive-command strings → risks flagged, Confidence **Low**

## How confidence is computed

- Any risk pattern found → **Low**
- No risks but large diff (>400 lines) or many files (>15) → **Medium**
- Otherwise → **High**

Heuristic review complements, not replaces, human judgement.

## License

MIT
