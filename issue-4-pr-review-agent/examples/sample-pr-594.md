## Claude Review

**PR**: perf(home): lazy-hydrate main bundle and lazy-load Vimeo for / ([#594](https://github.com/tailcallhq/tailcallhq.github.io/pull/594))
**Author**: @yasumorishima

### Summary of Changes
This PR updates `27` file(s) in `tailcallhq/tailcallhq.github.io` with `464` additions and `69` deletions. The main surface area is `docusaurus.config.ts, package-lock.json, package.json`. No dedicated test files changed, so behavior should be verified carefully.

### Identified Risks
- No explicit automated tests changed, which raises regression risk if runtime behavior changed.
- The diff appears to introduce secret-like strings or credential variables that should be double-checked.
- Destructive operations or removal-oriented logic appear in the diff and deserve a careful rollback review.
- The PR spans many files, which can hide cross-file integration mistakes.

### Improvement Suggestions
- Add or document at least one focused verification step so reviewers can confirm the intended behavior quickly.
- Consider calling out the highest-risk files in the PR description to speed up maintainer review.

### Confidence
Low
