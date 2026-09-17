# Pull request review

Source: https://github.com/pallets/click/pull/3866
Reviewed head: `eb37beaa493344e9fe6ef5ef7619d0c25c030177`

## Summary

The patch adds a \`\_outside\_click\_stacklevel\(\)\` frame-walking helper in src/click/core.py and a \`Parameter.\_check\_name\_is\_identifier\(\)\` method that emits a \`DeprecationWarning\` when a resolved parameter name is not a valid Python identifier; \`Option.\_parse\_decls\` invokes it on the \`not expose\_value\` path before returning an empty name. \`Option.\_parse\_decls\` now records the explicitly declared identifier as \`explicit\_name\` and warns through the new \`\_check\_name\_is\_normalized\(\)\` when it is not already lower-cased, while the former \`name = None\` reset for a non-identifier derived name is folded into the combined \`if name is None or not name.isidentifier\(\):\` guard; both deprecations are recorded in CHANGES.md and docs/upgrade-guides.md.

## Identified risks

- No specific defect established from the supplied diff; this is not proof of absence.

## Improvement suggestions

- No additional suggestions grounded in this diff.

## Confidence

Low

## Evidence limits

Diff-only review; no repository code, build, or tests were executed by this tool.

## Verification notes

- 8 hunk group\(s\) reviewed; 16 model calls. 0 candidate\(s\) excluded by source checks or audit; exact raw decisions are retained in verification.json when evidence is requested.
- Confidence is capped at Medium: matching quotes and model agreement are not runtime proof or a calibrated accuracy score. No recommendation is guaranteed correct.
