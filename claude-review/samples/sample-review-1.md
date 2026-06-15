## PR Review

### Summary
This PR introduces a complete TypeScript SDK (`@engram/client`) for the Engram decentralized vector database, mirroring the existing Python SDK. It adds 10 files with 920 lines of new code covering the core client, encryption (X25519 + AES-256-GCM), Shamir secret sharing, error types, and unit tests.

### Files Changed
| File | Lines | Type |
|------|-------|------|
| engram-ts/src/client.ts | +277/-0 | new |
| engram-ts/src/encryption.ts | +236/-0 | new |
| engram-ts/src/shamir.ts | +123/-0 | new |
| engram-ts/src/exceptions.ts | +50/-0 | new |
| engram-ts/src/__tests__/shamir.test.ts | +65/-0 | new |
| engram-ts/src/index.ts | +21/-0 | new |
| engram-ts/package.json | +27/-0 | new |
| engram-ts/tsconfig.json | +17/-0 | new |
| engram-ts/README.md | +100/-0 | new |
| engram-ts/.gitignore | +4/-0 | new |

### Identified Risks
- **Risk**: The encryption module uses Web Crypto API for AES-256-GCM which may not be available in all JavaScript runtimes (e.g., React Native).
  **Severity**: MEDIUM
  **File**: `engram-ts/src/encryption.ts`
  **Suggestion**: Add a fallback to `@noble/ciphers` for environments without Web Crypto.
- **Risk**: No automated CI pipeline is included in the PR — tests must be run manually.
  **Severity**: LOW
  **File**: `engram-ts/package.json`
  **Suggestion**: Add a `.github/workflows/ci.yml` with `npm ci && npm test`.

### Improvement Suggestions
- **Suggestion**: Add JSDoc comments to public methods
  **File**: `engram-ts/src/client.ts`
  **Why**: The Python SDK has detailed docstrings; the TS SDK should match for IDE autocompletion.
  **How**: Use `/** */` blocks on all public methods matching the Python docstring format.
- **Suggestion**: Improve error handling for network timeouts
  **File**: `engram-ts/src/client.ts`
  **Why**: The `fetch()` call uses `AbortSignal.timeout()` but doesn't differentiate between timeout and connection errors.
  **How**: Catch `AbortError` separately from other network errors.

### Strengths
- Clean separation of concerns: client, encryption, exceptions, and shamir in separate modules
- Pure JS crypto via `@noble/*` packages — no native dependencies, works everywhere
- Full test coverage for the Shamir module with 7 test cases
- Proper TypeScript configuration with strict mode enabled

### Confidence Score
**Confidence: High**
The code is well-structured, follows the Python SDK patterns closely, uses established crypto libraries, and includes passing tests. The architecture is clean and the TypeScript configuration is production-ready.
