# PR Review: 15498: Enable Pydantic polymorphic_serialization flag on response serialization

> https://github.com/fastapi/fastapi/pull/15499

## Summary
This PR adds a new `response_model_polymorphic_serialization` parameter to FastAPI path operations, enabling Pydantic's polymorphic serialization so that subclass-specific fields are included in responses even when the route is typed with a base-class response model. The change threads the flag through the entire decorator/router stack (`applications.py`, `routing.py`, `_compat/v2.py`) and adds comprehensive tests and documentation.

## Identified Risks
- **Hard Pydantic version dependency**: The feature silently no-ops on Pydantic < 2.13 (the `kwargs` dict is only extended on `>= 2.13`). A user enabling the flag on an older Pydantic version will get no error and no polymorphic output — this diverges from the explicit `ValueError` raised in `serialize()`, creating an inconsistent experience.
- **Large surface area (+560 lines)**: The parameter is added to every HTTP-method helper (`get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `trace`) and their corresponding `APIRouter` counterparts. A single missed callsite would produce a silent mismatch.
- **No deprecation path tested**: The PR doesn't show what happens if a user calls the endpoint with Pydantic 2.12 and `polymorphic_serialization=True`; the test suite presumably runs only on the CI Pydantic version.

## Improvement Suggestions
- Unify version-guard behaviour: either raise `ValueError` (like `serialize()` does) or silently ignore in both paths — don't mix the two.
- Add a CI matrix entry that runs the new test with Pydantic < 2.13 to confirm the fallback path.
- Consider a single shared helper (e.g. `_apply_polymorphic_kwarg`) to reduce copy-paste across `serialize`/`serialize_json` and avoid future drift.

## Confidence Score
Medium
