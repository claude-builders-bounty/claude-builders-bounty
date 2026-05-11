## PR Review

**PR:** https://github.com/fastify/fastify/pull/6239

### Summary

This sample demonstrates the expected structured output for a documentation-oriented PR. A documentation/tutorial diff should generally produce a short summary, low implementation risk, and suggestions focused on verifying links, examples, and command snippets.

Changed files:

- `docs/Reference/Tutorials.md`

### Identified Risks

- **Low:** Documentation examples can become stale; verify all command snippets and internal links before merge.

### Improvement Suggestions

- Run documentation checks if the repository provides them.
- Confirm that new tutorial content links to existing reference pages rather than duplicating long-lived API details.

### Confidence Score

**High**
