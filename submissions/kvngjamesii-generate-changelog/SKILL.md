---
name: generate-changelog
description: Generate a Keep a Changelog–formatted CHANGELOG.md from git history since the last tag. Use when the user runs /generate-changelog, asks to create or update a changelog, or wants commits grouped into Added / Fixed / Changed / Removed.
license: MIT
metadata:
  author: KvngJamesII
  bounty: "claude-builders-bounty#1"
  version: "1.0.0"
---

# /generate-changelog

Build a structured `CHANGELOG.md` from the current repo's git history.

## When to use

- User invokes `/generate-changelog`
- User asks to "write/update the changelog" or "summarize commits since the last release"

## Steps

1. Confirm you are inside a git work tree (`git rev-parse --is-inside-work-tree`).
2. Run the bundled script from this skill directory (or a copied path):

```bash
bash changelog.sh                 # writes/prepends CHANGELOG.md since last tag
bash changelog.sh --stdout        # preview only
bash changelog.sh v1.2.0 --stdout # explicit base ref
```

3. Show the generated Markdown. If `CHANGELOG.md` already existed, the script **prepends** a new Unreleased section under the title instead of wiping history.
4. Report commit count and the resolved range (tag → HEAD, or full history if untagged).

## Categorization rules

| Bucket | Conventional / keywords |
|--------|-------------------------|
| **Added** | `feat:`, `add:`, add/introduce/implement… |
| **Fixed** | `fix:`, `bugfix:`, `hotfix:`, fix/bug/patch… |
| **Changed** | `refactor:`, `perf:`, `style:`, `chore:`, `docs:`, `ci:`, update/improve/rename… |
| **Removed** | `remove:`, `delete:`, `revert:`, `drop:`, remove/delete/drop… |

Merge commits are skipped. Descriptions are cleaned of type prefixes and short hashes are kept.

## Constraints

- Read-only on git history — never amend, reset, or rewrite commits.
- Prefer Keep a Changelog section order: Added → Fixed → Changed → Removed.
- If there is no tag, use full history and label the section accordingly.
