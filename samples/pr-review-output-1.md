## PR Review Summary

Reviewed https://github.com/cli/cli/pull/13580. This PR changes **11 file(s)** with approximately **2460 added** and **0 removed** lines. The touched files are: acceptance/testdata/repo/repo-read-dir.txtar, acceptance/testdata/repo/repo-read-file.txtar, internal/text/text.go, internal/text/text_test.go, pkg/cmd/repo/read-dir/http.go, pkg/cmd/repo/read-dir/read_dir.go, pkg/cmd/repo/read-dir/read_dir_test.go, pkg/cmd/repo/read-file/http.go, and 3 more.

## Identified Risks
- Large change surface; split review by subsystem and require focused tests before merge.

## Improvement Suggestions
- Keep the PR focused and include command output from the relevant test suite in the final description.

## Confidence Score
**Medium**

