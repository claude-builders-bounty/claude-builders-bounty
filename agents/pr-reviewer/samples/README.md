# Sample Outputs

This directory contains review outputs generated from real public GitHub PRs and local fixture diffs. The set intentionally mixes local security/safe/dependency-impact fixtures, Python web libraries, and a large JavaScript framework workflow PR.

Regenerate real PR samples with:

```bash
claude-review --pr <pr-url> --output agents/pr-reviewer/samples/<name>.md
```

The exact risk wording is deterministic for a given diff and tool version. Real public PR samples can drift if the upstream PR branch changes before merge.
