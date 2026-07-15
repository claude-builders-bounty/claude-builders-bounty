# PR Review: sindresorhus/is-plain-obj#1

**Title:** switch to Object.getPrototypeOf  
**Author:** @schnittstabil  
**URL:** https://github.com/sindresorhus/is-plain-obj/pull/1  
**Diff:** +11 / -3 · 2 files  
**Engine:** local-heuristic

## Summary of changes

PR sindresorhus/is-plain-obj#1 ("switch to Object.getPrototypeOf") by @schnittstabil touches 2 file(s) (+11/-3): `index.js`, `test.js`. Author intent: Setting the `prototype.constructor` is often considered good practice for constructor functions, but also can be misused to break `is-plain-obj`. The review scanned the unified diff for security patterns, test-coverage signals, and change-size risk.

## Identified risks

- No high-severity risk patterns detected in the diff surface

## Improvement suggestions

- Diff looks focused; consider a short manual smoke test of the primary user path before merge.

## Confidence score

**High**
