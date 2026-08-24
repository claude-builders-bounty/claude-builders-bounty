# Sample Output

Generated from [cli/cli](https://github.com/cli/cli) between tags `v2.88.0..v2.89.0`:

```markdown
# Changelog

## [v2.89.0] — 2026-03-27

### Added

- feat(search): clear search input after submitting query (13e47d0)
- feat(search): add placeholder to search input (f38abbe)
- feat(survey): search-based assignee selection in MetadataSurvey (11f177a)

### Fixed

- fix: remove unused fields and imports (84a3ba8)
- fix: use synchronized accessors to eliminate data race (38e10d5)
- fix: update test expectations for huh v2 (95a59f4)
- fix(api): fetch nameWithOwner in headRepository GraphQL query (5ed8cf0)
- fix(test): set git identity in testscript sandbox (6666850)
- fix: use useReviewerSearch consistently in prompt path (391e661)
- fix(copilot): wire up @copilot assignee replacement and [bot] suffix (bff468b)
- fix(api): use login-based assignee mutation on github.com (e6d9019)
- fix(copilot): resolve Copilot API URL dynamically (#12956) (78b958f)
- fix(docs): improve docs around IssueRepoInfo (27fb2da)
- fix: use IssueRepoInfo to fetch minimal fields for issues (aad0239)
- fix(perms): use IssueRepoInfo to avoid requiring Contents:Read permission (1d95b63)

### Changed

- refactor(prompter): Ensure huh prompter cleans up (cb2b505)
- chore(deps): go mod tidy (f92fab6)
- refactor(ui): custom Field for MultiSelectWithSearch (cfb2224)
- refactor(test): pipe-based test harness with full coverage (4d74e05)
- refactor(ui): Upgrade to huh/v2 and fix selection persistence in MultiSelectWithSearch (f294831)
- style: Fix gofmt alignment for prompter-enabled fields in IOStreams (4661c05)
- refactor(ui): Use LayoutStack for huhPrompter MultiSelectWithSearch (726714d)
- feat(prompter): Add experimental huh-only prompter gated by GH_EXPERIMENTAL_PROMPTER (87426ee)
- chore(deps): bump github.com/zalando/go-keyring from 0.2.6 to 0.2.8 (c3fe99f)
- docs: Align triage.md with unified triage process (c82177c)
- refactor(api): simplify ApiActorsSupported in RepoMetadataInput (6a68ebc)
- refactor: rename ActorIsAssignable to ApiActorsSupported (ae5e857)
- refactor: consolidate ActorAssignees and ActorReviewers into ApiActorsSupported (3c00ffd)
- refactor(copilot): extract SpecialAssigneeReplacer for @me and Copilot expansion (4e6bc78)
- chore(deps): bump github.com/google/go-containerregistry (b99ee4c)
- feat(telemetry): Record agentic invocations in User-Agent header (c51769c)
- docs: Add AGENTS.md optimized for AI agent token efficiency (45596c9)

---

*40 commits in this release.*
```
