## PR Review: Turbopack: use same hash for immutable-static-hashes.json

### Summary
This PR fixes a performance regression introduced in #91137 where the `immutable-static-hashes.json` manifest was computing file content hashes separately from the hashes used for filenames, effectively doubling the hashing work. The fix changes the manifest to reuse the existing filename hash (`version_hash`) instead of re-hashing file contents via `content_hash`, and adds tests to verify the behavior works correctly with deployment IDs.

### Risk Assessment
- **Hash algorithm change**: Switching from `content_hash` to `version_hash` in `project_asset_hashes_manifest.rs` means the manifest values will differ from the previous format. Any downstream tooling or CDN invalidation logic that depends on the specific hash values in `immutable-static-hashes.json` may break. This is likely acceptable since it is a regression fix (restoring previous behavior), but should be verified against any consumers of this manifest.
- **Test coverage is narrow**: The new test (`deployment-id-handling.test.ts`) checks that static assets contain the deployment ID in their URLs and that the adapter receives the manifest, but does not explicitly verify that the hash in the manifest matches the hash in the filename. A mismatch would silently pass these tests.

### Suggestions
- **`project_asset_hashes_manifest.rs:L47`**: Consider adding a code comment explaining why `version_hash` is used instead of `content_hash`, referencing this PR and #91137. Future contributors may not understand the performance implication:
  ```rust
  // Use version_hash (same as filename hash) to avoid double-hashing file contents.
  // See: https://github.com/vercel/next.js/pull/92157
  ```
- **`deployment-id-handling.test.ts:L24`**: The new test assertions check `Object.keys(manifest).length > 0` but could be more specific. Consider asserting that at least one manifest key matches the pattern of a static asset path, and that the corresponding value matches the hash embedded in the filename:
  ```typescript
  const [path, hash] = Object.entries(manifest)[0];
  expect(path).toMatch(/\/_next\/static\//);
  expect(path).toContain(hash.slice(0, 8)); // hash appears in filename
  ```
- **`my-adapter.mjs`**: The test adapter writes the manifest to stdout, which is fine for testing but consider using `console.error` or a file to avoid polluting stdout in case other test assertions capture it.

### Confidence
**Score: High**
This is a small, focused change (1 line of Rust + 35 lines of tests) in a well-understood area (build asset hashing). The regression source is clearly identified and the fix is straightforward. The Rust change is a direct field substitution with no logic changes.

---
*Reviewed by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) v1.0.0*
