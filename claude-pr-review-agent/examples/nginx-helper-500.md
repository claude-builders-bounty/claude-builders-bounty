# PR Review: fix: load plugin textdomain on init instead of plugins_loaded

## Summary
This PR changes 100 file(s) with +187/-16522 lines. The main touched areas are:

- tests: 89 file(s), +0/-1517
- admin: 4 file(s), +144/-4
- .github: 3 file(s), +37/-68
- (root): 2 file(s), +2/-2
- includes: 2 file(s), +4/-3

Based on the PR metadata and diff, the change appears focused on: fix: load plugin textdomain on init instead of plugins_loaded.

## Identified Risks
- Large change set; review should be split by subsystem or backed by stronger test evidence.
- Security- or payment-sensitive files changed; verify authorization, input validation, logging, and secret handling.
- Diff contains TODO/FIXME markers; confirm they are acceptable before merge.

## Improvement Suggestions
- Ask reviewers to focus on the highest-risk changed areas listed above.

## Confidence Score
Medium

## Review Metadata
- PR: https://github.com/rtCamp/nginx-helper/pull/500
- Base: develop
- Head: fix/load-textdomain-on-init
- Head SHA: 626f474d88f0c12564e930c005b15360d742b2b8
