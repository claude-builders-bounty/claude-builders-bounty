# PR Review: https://github.com/openclaw/openclaw/pull/1

## Summary
This PR introduces support for WhatsApp's newer `@lid` (Linked ID) format by adding a reverse mapping lookup in `jidToE164()`, and fixes a logic bug where the `allowFrom: ["*"]` wildcard configuration failed to match any senders due to strict equality checks.

## Risks
- Synchronous file I/O (`fs.readFileSync`) is introduced in the `jidToE164()` function, which could block the Node.js event loop and degrade throughput under high message volumes.
- Silent failure in the `catch` block when a `@lid` mapping file is not found means degraded functionality (messages dropped) could be difficult to diagnose in production without verbose logging enabled.
- The `@lid` regex captures the full LID string, but the reverse mapping file name interpolation relies on an undocumented assumption that the JSON file contains a bare number string at its root.

## Suggestions
- Replace `fs.readFileSync` with `fs.promises.readFile` (and update `jidToE164` to be `async`) to prevent blocking the event loop during inbound message processing.
- Add a debug or warning log inside the `catch` block (e.g., `logVerbose("LID mapping not found for...")`) to aid in troubleshooting when LIDs fail to resolve.
- Validate the parsed JSON payload from the reverse mapping file to ensure it is a string of digits before prepending the `+` sign, preventing malformed outputs like `+[object Object]`.

## Confidence: High
The changes are highly targeted, minimal in scope, and directly address well-documented bugs with clear backward compatibility.
