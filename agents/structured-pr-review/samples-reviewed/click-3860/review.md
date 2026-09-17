# Pull request review

Source: https://github.com/pallets/click/pull/3860
Reviewed head: `05f6fd0df4ecbd104eb7a229f9f185c2484dee69`

## Summary

This PR changes the help output so that the 'Positional arguments' section appears whenever at least one argument has a help string, and then lists ALL arguments regardless of whether they have help text. Previously, \`Argument.get\_help\_record\(\)\` returned \`None\` for undocumented arguments, causing them to be omitted from help. Now it always returns a tuple with an empty description for undocumented arguments.

## Identified risks

- **Medium** | src/click/core.py: The change to \`get\_help\_record\(\)\` returning an empty string instead of \`None\` is a breaking change for help output. Users who relied on undocumented arguments being hidden from help will now see them listed with empty descriptions, which may affect documentation clarity or help text expectations.
- **Low** | src/click/core.py: The condition \`if any\(arg.help is not None for arg in args\)\` determines when the section appears. This means a command with only undocumented arguments will not show the 'Positional arguments' section at all, which could be unexpected for users expecting to see all arguments in help.

## Improvement suggestions

- Consider adding a deprecation warning for the old behavior where \`get\_help\_record\(\)\` returned \`None\` for undocumented arguments.
- The documentation updates in docs/arguments.md and docs/documentation.md accurately reflect the new behavior and are sufficient.
- The test coverage is comprehensive and validates the new behavior across multiple scenarios including None, empty string, and documented help.

## Confidence

Medium

## Evidence limits

Diff-only review; no repository code, build, or tests were executed by this tool.
