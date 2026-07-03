# Issue #2853 verification session diffs

`tests/verify-issue-2853.sh` archives working-tree patches here before and after each
verification phase (`start`, `post-npm-test`, `complete`, or `failed`). Patches are
gitignored (local-only) to keep the PR diff reviewable; re-run the script to regenerate.

Patches are named `session-<timestamp>-<label>-<phase>.patch`.

## Script usage

```bash
bash tests/verify-issue-2853.sh
make verify-issue-2853
npm run test:verify-issue-2853
```

The script validates `ZEROEYE_BRANCH`, `ZEROEYE_REPO`, `ZEROEYE_ROOT`, and
`VERIFY_SESSION_LABEL` before cloning. Defaults clone `advancedresearcharray/zeroeye`
branch `pr-3-read-tool-hook` into `.cache/zeroeye-pr-3-read-tool-hook`, run `npm test`,
then `npm run test:issue-2853`.
