## Summary

ci: integrate typos spell checker into CI workflow changes 13 files with 108 added lines and 22 removed lines. The main touched paths are .github/workflows/typos.yaml, _typos.toml, cmd/tmc/main.go, internal/runner/runner.go, internal/server/server.go. There are 8 more changed files beyond that.

## Risks

- Authentication code changed; reviewers should check permissions and token handling.
- GitHub workflow changes can affect CI or repository automation.
- Delete behavior changed; check data loss paths.

## Suggestions

- Include one run or screenshot showing the workflow passes on the target branch.
- Add a focused test or manual proof for the highest-risk path.

## Confidence

Medium
