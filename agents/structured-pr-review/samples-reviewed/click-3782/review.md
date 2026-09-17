# Pull request review

Source: https://github.com/pallets/click/pull/3782
Reviewed head: `a92dddb95d1fe01b8e2ace6e215aef690d369188`

## Summary

This PR adds a \`break\_on\_hyphens\` parameter to \`wrap\_text\(\)\` in \`src/click/formatting.py\` to prevent usage line arguments from being split at hyphens. The \`HelpFormatter.write\_usage\(\)\` method now passes \`break\_on\_hyphens=False\` when wrapping option names and metavar values, addressing issue \#3362. Tests verify that hyphenated option names stay on one line while the default behavior for general text wrapping remains unchanged.

## Identified risks

- No specific defect established from the supplied diff; this is not proof of absence.

## Improvement suggestions

- No additional suggestions grounded in this diff.

## Confidence

High

## Evidence limits

Diff-only review; no repository code, build, or tests were executed by this tool.
