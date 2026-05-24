### Summary
This PR introduces `changelog.sh`, a bash script designed to generate a `CHANGELOG.md` file by parsing the local git history. It categorizes commits based on conventional commit prefixes (e.g., `feat:`, `fix:`, `revert:`) and provides several CLI options for specifying tags, ranges, and output directories.

### Risks
- **Requirement Violation:** The bounty issue explicitly requested a "Python script" to generate the structured CHANGELOG. Submitting a bash script directly violates the primary requirement, which may lead to immediate rejection by the maintainer.
- **Portability Issues:** Bash scripts heavily rely on the availability and consistent behavior of coreutils (like `sed`, `awk`, `grep`) across different platforms (macOS vs. Linux), which can lead to unpredictable generation bugs.
- **No major security risks identified.**

### Suggestions
- **Rewrite in Python:** Completely rewrite the logic using Python. Leverage the built-in `subprocess` module to call git or use the `GitPython` library for a more robust, cross-platform implementation.
- **Enhanced Parsing Logic:** Python allows for more complex parsing and templating mechanisms compared to bash string manipulation, enabling richer changelog generation (e.g., grouping by author, detecting breaking changes properly).

### Confidence
High
