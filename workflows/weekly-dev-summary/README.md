# Weekly GitHub development summary

An importable n8n workflow that collects the last seven days of default-branch
commits, closed issues, and merged pull requests; asks Claude for an English or
French narrative; and sends the result to Discord.

## Setup in five steps

1. Import `workflow.json` into n8n. The export is inactive. Verified engine:
   n8n 2.39.6; the workflow timezone is `America/New_York`.
2. Edit the Configuration node: `owner/repository`, `EN` or `FR`, model, and
   your Discord webhook URL. The model defaults to `claude-sonnet-4-6`; see
   `MODEL-NOTE.md` for the retired model in the original bounty.
3. Create two n8n Header Auth credentials. For GitHub, use header
   `Authorization` with your `Bearer ...` token and assign it to all three
   GitHub HTTP nodes. For Claude, use `x-api-key` with your Anthropic key and
   assign it to Claude Summary. Credentials are not embedded in the export.
4. Run Manual Start and inspect collection counts, model output, and Discord
   delivery. More than ten response pages, incomplete search results, or
   truncated model output stop delivery rather than silently losing evidence.
5. Activate the workflow after that live manual check. The weekly trigger runs
   Fridays at 17:00 in the configured workflow timezone. Change it as needed.

## Verification

- 26 code-level tests passed, including pagination/count handling, English/French
  configuration, empty input, Discord chunking, and n8n task-runner compatibility.
- Five real n8n engine scenarios passed against **synthetic HTTP services**:
  English, French, empty week, incomplete GitHub search, and truncated Claude
  output. The two negative scenarios stopped without sending a message.
- Live public GitHub validation also passed: 2 commits, 2 closed issues, and 13
  merged PRs in the tested window. Model/delivery were still synthetic.
- No live Anthropic request or real Discord delivery is claimed.
- The actual n8n editor screenshot is included in `engine-evidence/`. It shows
  successful execution with visibly labeled synthetic external services.

See `TESTING.md` and `engine-evidence/README.md` for reproduction and limits.
Run the code-level suite with `node --test test/workflow.test.cjs`.

## Behavior and limits

The model receives source metadata and explicit counts, not entire diffs.
Evidence is limited to 150 records of each kind and omissions are disclosed.
Commit collection is for the default branch; PR merge timestamps use GitHub's
`merged:` search filter. Repository text is treated as data, not instructions.
Discord messages are chunked and mentions are disabled. There are no automatic
retries on model calls or message sends. Delivery is not transactionally
exactly-once; inspect Discord before manually replaying a failed delivery.
