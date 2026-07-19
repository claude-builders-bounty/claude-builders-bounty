## Summary

This PR fixes three root-cause bugs in the DSN parser that prevented Smoothie Board conversion: `(rotate N)` modifier was misread as pin number, coordinate parsing started at the wrong index when the modifier was present, and `Number()` coercion produced NaN for non-numeric pin labels like `A`, `C`, `+`, and `-`.

## Identified Risks

- The `coordStartIndex` calculation assumes `(rotate N)` is always at `nodes[2]` — if other List modifiers are added in the future, this may break
- Setting `pin_number` to `undefined` for non-numeric labels may break downstream consumers that expect a number — verify all consumers handle `undefined`
- The `getPinNum` function still returns string for non-numeric pins, but the component converter now silently drops the pin number — consider logging a warning

## Improvement Suggestions

- Generalize the `(rotate N)` skip logic to handle any List modifier, not just `rotate`
- Add a warning log when pin_number is set to `undefined` due to non-numeric label
- Consider mapping non-numeric pin labels to a numeric index (e.g., A=1, B=2) as a fallback

## Confidence Score

**Medium** — The fixes address real bugs with good test coverage, but the `undefined` pin_number change could have downstream effects that need validation.
