# Changelog

All notable changes to **meteor** since release/METEOR@3.4.

## [release/METEOR@3.4] — 2026-04-28

### Changed

- 8a96739f96 Fix getUsersInRoleAsync dropping 'user' field when queryOptions.fields is set
- 39a96611cd Merge pull request #14364 from meteor/cherrypick-group-5-fix
- 17d6919311 Merge pull request #14352 from meteor/dependabot/github_actions/actions/upload-artifact-7
- 7ac17f2649 Merge pull request #14334 from meteor/dependabot/github_actions/actions/github-script-9
- 6b877fd870 cherrypick fix on group 5 by simplify environment variable overrides and match assertions
- f34e7ef0b6 Merge pull request #14361 from mvogttech/fix(mongo)--make-observeChangesAsync-callback-error-test-deterministic
- 4f074c1bce Merge branch 'fix(mongo)--make-observeChangesAsync-callback-error-test-deterministic' of https://github.com/mvogttech/meteor into fix(mongo)--make-observeChangesAsync-callback-error-test-deterministic
- 5eb2df51b7 re-run checks
- 223e01a8b7 Merge branch 'devel' into fix(mongo)--make-observeChangesAsync-callback-error-test-deterministic
- 099fefdbcd fix(mongo): make observeChangesAsync callback-error test deterministic
- 809fd362e0 chore(deps): bump actions/github-script from 8 to 9
- 1bfcb7500b chore(deps): bump actions/upload-artifact from 4 to 7
- c1fa742bca Merge pull request #14353 from meteor/fix-flakiness-timeout
- d1e46e07d5 adjust TIMEOUT_SCALE_FACTOR values in test-tools workflow configuration
- 0a33bdf271 swap CPU/memory/seccomp options within test-tools workflow configuration
- c6dd463f9b update test-tools workflow: allocate 4 CPUs, 16GB memory, and disable seccomp for container
- 8242189321 increase TIMEOUT_SCALE_FACTOR to 14 for self-tests optimization
- ef359af77e Merge pull request #14351 from meteor/ci/removing-travis-and-circle
- b54df7c753 CI: removing circle CI
- 92c04d5436 Merge pull request #14326 from meteor/ci/removing-circleci
- 73f172507d Merge pull request #14337 from meteor/gh/code-owners
- 96ddb1a921 Merge branch 'devel' into gh/code-owners
- f8ad963055 Merge pull request #14341 from meteor/docs/update-hostname
- 9cb75cd529 docs: update EU region DEPLOY_HOSTNAME URL in deployment guide
- 3fd0ff17c4 Update deployment hostname for Meteor app
- 9b9564cc28 chore: add wildcard to CODEOWNERS to include all contributors
- 6882a92b5e chore: update GitHub username casing for @grubba27 in CODEOWNERS
- 9f7816d05d chore: update code owners list for repository maintenance
- 1f745b78fd Merge pull request #14309 from meteor/oxc/phase-1
- 788147e444 chore: generate and update package change history JSON output
- f8a371e6ea feat: add script to map packages to their associated pull requests and generate tracking data
- 684ca39eed Merge branch 'devel' into oxc/phase-1
- 3cbd04510d Merge pull request #14320 from meteor/ts/type-coverage-setup
- 818ab002d6 chore: update type-coverage workflow to use oss-vm runner
- 097d40251b Merge branch 'devel' into ts/type-coverage-setup
- e62868f52a docs: update breadcrumb comment to remove inaccurate percentage reference
- 16190a226a Merge branch 'devel' into oxc/phase-1
- c554fd354f DEV: testing w/docker 5
- dd3695a1a6 DEV: testing w/docker 4
- ae1d9bd299 DEV: testing w/docker 3
- bdb3c03443 DEV: testing w/docker 2
- d880f35485 DEV: testing w/docker
- 9b54f684e6 DEV: testing something
- f5b5cdacf8 CI: move circleci to GitHub actions
- 39c2acd43b Merge pull request #14325 from meteor/docs-fix-changelog-dates
- 25360fba00 Merge branch 'devel' into docs-fix-changelog-dates
- 743df1d337 DOCS: fix generator
- 976b2689ec Merge pull request #14300 from meteor/ci/removing-travis
- 8f3e4a5fb8 Merge branch 'devel' into ci/removing-travis
- 3c245af288 fix: update date format in history.md for consistency
- 5f50d759d3 style: fix indentation and formatting in sunburst.js
- 36f9060a25 Merge branch 'devel' into oxc/phase-1
