# Pull request review

Source: https://github.com/pallets/click/pull/3782
Reviewed head: `a92dddb95d1fe01b8e2ace6e215aef690d369188`

## Summary

This PR adds a \`break\_on\_hyphens\` parameter to \`wrap\_text\` in \`src/click/formatting.py\`, defaulting to \`True\` to maintain backward compatibility. It modifies \`HelpFormatter.write\_usage\` to pass \`break\_on\_hyphens=False\` when wrapping usage line arguments, ensuring option names and metavar values are not split across lines at hyphens. New tests verify that hyphenated arguments remain intact and that lines do not end with hyphens.

## Identified risks

- No specific defect established from the supplied diff; this is not proof of absence.

## Improvement suggestions

- The PR includes a \`.. versionchanged:: 8.5.0\` marker in the docstring for \`wrap\_text\`, but the \`CHANGES.md\` entry references version 8.5.0 without a corresponding \`\#\# Version 8.5.0\` section header. This should be added to maintain consistency with the changelog format.
- The test \`test\_write\_usage\_keeps\_hyphenated\_args\_whole\` uses \`any\(option in line for line in lines\)\` to verify option presence, which is less precise than checking for exact line matches. A direct assertion like \`assert option in lines\[0\]\` would be clearer.
- The PR does not include a binary patch, but the diff text appears complete. Confidence is based on the provided patch content rather than any missing binary data.

## Confidence

High

## Evidence limits

Diff-only review; no repository code, build, or tests were executed by this tool.
