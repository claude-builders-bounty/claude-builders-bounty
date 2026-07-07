## PR Review

> **PR**: claude-builders-bounty/claude-builders-bounty#25
> **Title**: feat: PR reviewer agent with structured Markdown output (Bounty #4)
> **Author**: @ElromEvedElElyon

### Summary
This PR proposes a full bounty submission for the PR reviewer agent by adding six new artifacts, including agent assets, a shell entrypoint, a workflow file, prompt content, and sample review outputs. Based on the visible diff, the implementation is documentation- and scaffolding-heavy, with the first sample output showing the intended review format and tone.

### Identified Risks
- The visible sample output does not cleanly match the bounty's required output contract. It uses `# PR Review:` and `## Confidence Score` instead of the simpler required section names, which creates acceptance risk even if the reviewer quality is otherwise fine.
- The PR appears to rely on generated examples and scaffolding, but the visible diff does not show evidence of two real GitHub PR review outputs tied to actual runs. That is a direct risk against the bounty acceptance criteria.
- The file set suggests a shell-based workflow (`claude-review.sh`, `pr-review.yml`) rather than a clearly validated Claude Code sub-agent flow. If the runtime assumptions are not documented precisely, reproducing the submission may be difficult.
- No automated verification is visible from the changed-files header, and the PR shows `Checks 0`. For a tool that promises a specific Markdown structure, missing smoke tests increases the risk of drift between examples and actual output.

### Improvement Suggestions
- Align the generated review format exactly with the bounty spec: `## PR Review`, `### Summary`, `### Identified Risks`, `### Improvement Suggestions`, and `### Confidence` with a single `Low | Medium | High` value.
- Replace synthetic examples with two real captured outputs from public GitHub PRs, and reference those runs directly in the PR description so maintainers can verify the claim quickly.
- Add a minimal smoke test that validates the required headings and confidence field, so the submission proves it can keep the contract stable.
- Document the execution path more concretely: prerequisites, how the shell script invokes Claude Code, what inputs it expects, and how failures are surfaced.

### Confidence
Medium
