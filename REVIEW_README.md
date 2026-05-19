# claude-review

Autonomous PR reviewer — analyzes GitHub PRs and returns structured Markdown review.

## Install

```bash
cp claude-review /usr/local/bin/
chmod +x /usr/local/bin/claude-review
export GH_TOKEN="your_github_token"
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

## What it checks

- Credentials in diffs (secret/password/token)
- Destructive SQL (DROP TABLE, TRUNCATE)
- Dangerous commands (recursive delete)
- Debug artifacts (console.log)
- Unresolved markers (TODO, FIXME)
- PR size (files > 15, additions > 500)

## Output

Structured Markdown with Summary, Risks, Suggestions, and Confidence score (Low/Medium/High).

## Sample

`claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1713`

```
# PR Review: feat: add structured CHANGELOG generator
PR: claude-builders-bounty/claude-builders-bounty#1713
Summary: +102 lines across 3 files

## Identified Risks
- No obvious risks detected.

## Assessment
Confidence: High — No risky patterns detected.
```
