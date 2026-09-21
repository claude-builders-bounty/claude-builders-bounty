# Sample review — the-tcpdump-group/libpcap#1752

Source PR: https://github.com/the-tcpdump-group/libpcap/pull/1752

## Summary
This PR adds an iterative control-flow-graph depth preflight before libpcap's recursive optimizer passes, rejecting graphs deeper than 128 nodes before they can exhaust the C stack. The traversal tracks the greatest observed depth for shared DAG nodes, grows its explicit stack safely, and deliberately lets an unexpected cycle exceed the threshold and fail closed.

## Risks
- The fixed depth limit of 128 can reject very deeply nested but otherwise valid filters that previously reached the optimizer, so the compatibility tradeoff depends on how representative that threshold is across supported platforms.
- `block->level` is reused as preflight scratch state; the patch relies on the later `find_levels()` pass recomputing it before any consumer reads those values.

## Improvement Suggestions
- Keep a regression fixture at the acceptance boundary, with one graph just below the threshold and one above it, so future optimizer refactors preserve the stack-safety contract.
- Document why 128 is an appropriate cross-platform ceiling, or centralize the constant with the optimizer's other complexity limits so the policy is easier to audit.

## Confidence
High
