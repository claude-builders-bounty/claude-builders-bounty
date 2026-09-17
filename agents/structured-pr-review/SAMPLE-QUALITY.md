# Current validation and historical failures

The sections below preserve the earlier local-model results. They describe those
recorded versions, not the final native profile. Current evidence, exact commands
and source-based assessment are under `validation/current/`. No historical raw
model output has been silently rewritten into a successful sample.

# Executed samples: integration success is not review accuracy

The two adjacent sample folders contain actual, unedited output from Claude Code
2.1.274 reviewing the live GitHub PR revisions recorded in each input packet.
The inference backend was local Ollama qwen3.5:4b through a temporary text-only
Messages adapter. It was not Anthropic-hosted inference and was not a mocked or
manually supplied review. Both full CLI executions exited 0 and produced all
requested sections. Thirty-three deterministic implementation tests also pass.

## Findings from checking the generated reviews against their inputs

The small local model's output is NOT reliable enough to publish unattended:

- Click #3866: the suggestion that Windows environment-name differences are
  documented but not tested is contradicted by the supplied tests. They compute
  platform-dependent expectations and assert both behavior branches. Its summary
  also overgeneralizes invalid identifiers: digits are invalid in the leading
  position, not every position.
- Click #3782: an Unreleased changelog entry does not need an already-created
  release heading. The suggestion to put every option on `lines[0]` contradicts
  the wrapping scenario; checking whole option presence on some line is relevant.
- Both generated confidence labels are High. Those are model self-assessments,
  not validated correctness scores, and are too strong for these samples.

These observations are preserved alongside the raw samples rather than editing
model errors away. The summaries describe the broad changes, but several
suggestions are false or unjustified. Accordingly the submission remains a
**draft requiring review-quality validation**, not a completed bounty claim.
A stronger available model and/or an evidence-checking review pass must resolve
this before treating the generated comments as dependable recommendations.

## Earlier integration issues actually repaired

The runner rejected invented out-of-hunk line references, preserving a useful
validation boundary. It was then improved to accept one JSON code fence (but not
surrounding prose or multiple blocks), because actual model responses used that
format. New tests cover all three cases. It still validates the output schema,
changed paths, and supplied hunk lines and never posts a review itself.

## Cost provenance

The CLI estimated dollars using an unrecognized model's fallback accounting.
Those estimates are retained in raw receipts for provenance only. They are not
cloud charges, a provider invoice, or the cost of local electricity/hardware.
The actual local inference records show model, token counts and elapsed time.

## Reproduction

With a working authenticated Claude Code installation, run the README command
against each recorded PR. To compare exactly, use the same pinned head revision
and inspect the packet hash. The local test configuration used Ollama qwen3.5:4b,
16,384 context tokens, no tools, no thinking and a 1,400-token output limit. Model
outputs vary; do not compare prose text hashes as if they were deterministic.

## Two-pass follow-up

The current runner performs an independent source-against-draft verification
pass. All 34 deterministic tests pass, including a check that the second prompt
receives both the source and draft rather than merely repeating the first request.

Actual two-pass runs completed on Click #3782 and #3860. Both pinned packets,
final unedited output and two-call provider metadata are in `samples-reviewed/`.
The #3782 output no longer contains the previously false release-heading and
wrapping-test suggestions. The #3860 summary broadly tracks the actual change,
but a risk incorrectly describes get_help_record as returning an empty string:
it returns a tuple whose second element may be empty. It also treats intended
unchanged omission of an all-undocumented help section as a speculative risk.
Its suggestions mix advice with praise. These are not reliable blocker findings.

The bigger #3866 request exceeded the local backend's 210-second inference wait.
That timeout is retained, not counted as a completed review. The two successful
smaller runs are integration evidence, not proof of broad accuracy or throughput.

The draft status remains intentional. No generated review was posted to either
Click PR, and no inaccurate sample was silently replaced with hand-written prose.
