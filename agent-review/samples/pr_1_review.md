**Summary of changes**:
This PR updates the dependency versions in the `package.json` file and modifies the `build.sh` script to use a new caching mechanism. It primarily aims to improve CI build times.

**Identified risks**:
- The updated version of `express` has known breaking changes.
- The cache directory in `build.sh` is not being cleaned, which might lead to disk space exhaustion on long-running runners.

**Improvement suggestions**:
- Add a cleanup step at the end of `build.sh` to remove stale cache files.
- Double-check the breaking changes in `express` and ensure all route handlers are still compatible.

**Confidence score**: High