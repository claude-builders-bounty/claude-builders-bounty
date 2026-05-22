## Summary
This PR adds Node.js v26 to the CI test matrix in `.github/workflows/ci.yml` and upgrades Mocha from `^10.7.3` to `^11.7.5` in `package.json`. The changes enable Express to be tested against the latest Node.js release and use a more recent version of the test framework.

## Risks
- **Mocha major version bump**: Upgrading from v10 to v11 in `package.json` is a major version change that may introduce breaking changes in test behavior or API. No changelog reference or test validation results are provided in the PR.
- **Untested compatibility**: There is no evidence in the diff that the test suite has been run against Node.js v26 or Mocha v11.7.5 to verify compatibility before merging.
- **Missing deprecation timeline**: The PR lacks context on Node.js v26's release status and support window, which should inform whether this is an urgent addition or can wait for stabilization.

## Suggestions
- Add a PR description explaining the motivation for the Mocha upgrade and confirm it passes all existing tests locally before merging.
- Consider separating the Node.js v26 CI addition from the Mocha version bump into two commits/PRs to isolate potential issues and make bisecting easier if problems arise.
- Reference the Node.js release schedule comment already in the workflow (line 48) by adding similar context to justify why v26 is being added now.

## Confidence: Medium
The individual changes are straightforward and low-complexity, but the lack of PR description, combined with an untested major dependency upgrade, creates uncertainty about whether these changes have been validated together.
