# claude-review

Analyze a GitHub PR and output a **structured Markdown review** in one command.

## Setup (1 command)

```bash
pip install -r requirements.txt   # or: no deps needed (stdlib only)
```

No dependencies beyond Python 3.9+. For **public repos** no token is needed; for private repos set `GH_TOKEN`:

```bash
export GH_TOKEN=ghp_xxx
```

## Usage

```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123
python claude-review.py --pr owner/repo#123 --output review.md
```

## Output format

- **Summary** — 2–3 sentences: what changed, additions/deletions, file count
- **⚠️ Identified Risks** — hardcoded credentials, debug output, bare excepts, destructive SQL, unsafe eval/shell=True, sensitive config files, oversized PRs
- **💡 Improvement Suggestions** — missing tests, docs, types
- **🎯 Confidence Score** — Low / Medium / High (based on change size)

## Tested on real PRs

Sample outputs included in this PR: `sample-review-pr1.md`, `sample-review-pr2.md` (generated from two real GitHub PRs).
