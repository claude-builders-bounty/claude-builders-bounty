# Pull request review

Source: https://github.com/pallets/click/pull/3782
Reviewed head: `a92dddb95d1fe01b8e2ace6e215aef690d369188`

## Summary

wrap\_text gains an opt-in break\_on\_hyphens parameter defaulting to True that is forwarded to the underlying text wrapper, leaving existing help-text wrapping unchanged. HelpFormatter.write\_usage passes break\_on\_hyphens=False in both of its wrapping branches, and tests assert no usage line ends in a hyphen for both the shared-prefix and below-prefix layouts.

## Identified risks

- No specific defect established from the supplied diff; this is not proof of absence.

## Improvement suggestions

- No additional suggestions grounded in this diff.

## Confidence

Medium

## Evidence limits

Diff-only review; no repository code, build, or tests were executed by this tool.

## Verification notes

- 1 hunk group\(s\) reviewed; 2 model calls. 0 candidate\(s\) excluded by source checks or audit; exact raw decisions are retained in verification.json when evidence is requested.
- Confidence is capped at Medium: matching quotes and model agreement are not runtime proof or a calibrated accuracy score. No recommendation is guaranteed correct.
