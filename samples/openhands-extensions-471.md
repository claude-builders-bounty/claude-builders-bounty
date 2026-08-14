# Review: feat: add Taskmarket delegation plugin

PR: https://github.com/OpenHands/extensions/pull/471

## Summary

This pull request, **#471 — feat: add Taskmarket delegation plugin**, changes 10 files (+574/-2).
The visible change surface includes `README.md`, `marketplaces/openhands-extensions.json`, `plugins/taskmarket-delegation/.claude-plugin`, `plugins/taskmarket-delegation/.codex-plugin` and other files.

## Identified risks

- **High:** dynamic or shell execution appears in the patch; validate inputs and constrain the execution boundary.

## Improvement suggestions

- Run the repository's formatter, linter, and full test suite before merging.

## Confidence

High

