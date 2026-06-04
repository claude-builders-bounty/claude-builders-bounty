## Claude PR Review

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2457

### Summary
This PR introduces a `changelog.sh` bash script that auto-generates a `CHANGELOG.md` by classifying commits since the last git tag into Added/Fixed/Changed/Removed sections using conventional-commit prefix matching. Supporting changes include a README section explaining usage and a committed initial `CHANGELOG.md` as the first generated output.

### Identified risks
- Bash 4.3+ required for 'local -n' (nameref): macOS ships bash 3.2 by default; running the script there will produce a cryptic error with no user-facing explanation.
- Committed CHANGELOG.md will be immediately stale: it captures only 'initial README with bounty board' but any future commit not re-running the script leaves the file out of date, which is potentially more misleading than no changelog at all.
- Merge commits are included: git log has no --no-merges flag, so 'Merge pull request #N from …' lines appear under Changed on every merge-heavy repo.
- Wildcard substring patterns (e.g., *' fix '*, *' bug '*, *' remove '*) can misclassify commits: a subject like 'add workaround to fix memory issue' contains ' fix ' and lands in Fixed instead of Added.
- Silent clobber of existing output file: if CHANGELOG.md already has hand-edited content the script overwrites it with no warning or backup.
- Tab character in a commit subject breaks IFS=$'\t' splitting, causing the hash to be appended to the subject or the entry to be skipped silently.
- Case-sensitive 'revert: ' prefix strip in clean_subject: 'Revert: …' (capital R, common from GitHub's auto-generated revert commits) is not stripped.

### Improvement suggestions
- Add 'Requires bash 4.3 or later' to the README instructions, or replace 'local -n' with an indirect expansion workaround (e.g., eval) for portability.
- Add --no-merges to the git log invocation to exclude merge commits from the changelog.
- Remove or tighten the substring wildcard patterns (*' fix '*, *' remove '*, *' bug '*) — conventional-commit prefix matching alone is safer and less ambiguous.
- Guard against clobbering an existing file: check if '$output_file' exists and prompt the user or require a '--force' flag before overwriting.
- Make the 'revert: ' strip case-insensitive, e.g. using a parameter expansion pattern or 'shopt -s nocasematch' around that line.
- Consider not committing the generated CHANGELOG.md (add it to .gitignore) and instead generating it as part of a release workflow, so the repo doesn't carry a perpetually stale artifact.

### Confidence score
High
