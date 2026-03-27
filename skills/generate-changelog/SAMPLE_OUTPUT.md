# Sample Output

Generated from [cli/cli](https://github.com/cli/cli) between tags `v2.88.0..v2.89.0`:

```markdown
# Changelog

## [Unreleased] (since v2.88.0)

### Added

- clear search input after submitting query (`13e47d0`)
- add placeholder to search input (`f38abbe`)
- search-based assignee selection in MetadataSurvey (`11f177a`)

### Fixed

- remove unused fields and imports (`84a3ba8`)
- use synchronized accessors to eliminate data race (`38e10d5`)
- update test expectations for huh v2 (`95a59f4`)
- fetch nameWithOwner in headRepository GraphQL query (`5ed8cf0`)
- set git identity in testscript sandbox (`6666850`)
- use useReviewerSearch consistently in prompt path (`391e661`)
- wire up @copilot assignee replacement and [bot] suffix (`bff468b`)
- use login-based assignee mutation on github.com (`e6d9019`)
- resolve Copilot API URL dynamically (#12956) (`78b958f`)
- improve docs around IssueRepoInfo (`27fb2da`)
- use IssueRepoInfo to fetch minimal fields for issues (`aad0239`)
- use IssueRepoInfo to avoid requiring Contents:Read permission (`1d95b63`)

### Changed

- Ensure huh prompter cleans up (`cb2b505`)
- go mod tidy (`f92fab6`)
- custom Field for MultiSelectWithSearch (`cfb2224`)
- pipe-based test harness with full coverage (`4d74e05`)
- Upgrade to huh/v2 and fix selection persistence in MultiSelectWithSearch (`f294831`)
- Fix gofmt alignment for prompter-enabled fields in IOStreams (`4661c05`)
- Use LayoutStack for huhPrompter MultiSelectWithSearch (`726714d`)
- Add experimental huh-only prompter gated by GH_EXPERIMENTAL_PROMPTER (`87426ee`)
- bump github.com/zalando/go-keyring from 0.2.6 to 0.2.8 (`c3fe99f`)
- Align triage.md with unified triage process (`c82177c`)
- simplify ApiActorsSupported in RepoMetadataInput (`6a68ebc`)
- rename ActorIsAssignable to ApiActorsSupported (`ae5e857`)
- consolidate ActorAssignees and ActorReviewers into ApiActorsSupported (`3c00ffd`)
- extract SpecialAssigneeReplacer for @me and Copilot expansion (`4e6bc78`)
- bump github.com/google/go-containerregistry (`b99ee4c`)
- Record agentic invocations in User-Agent header (`c51769c`)
- Add AGENTS.md optimized for AI agent token efficiency (`45596c9`)
```
