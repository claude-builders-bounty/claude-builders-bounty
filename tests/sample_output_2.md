### Summary of Changes
This pull request fixes a fatal null pointer dereference crash in the FalkorDB query AST compiler. It adds explicit support for the `AL_EXP_POW` operation to both the `_AlgebraicExpression_SrcOperand` and `_Pushdown_TransposeOperation` recursive evaluator functions.

### Identified Risks
- None identified. The logic matches the structurally equivalent `AL_EXP_ADD` operation, correctly propagating source aliases and pushing down transpositions for matrix power variables without side effects.

### Improvement Suggestions
- Consider adding an explicit `AL_EXP_POW` unit test or regression query test to the module's test suite to ensure this bug is never reintroduced.
- The default `ASSERT(false)` fallback is unsafe in production; consider replacing it with an error code propagation mechanism instead of crashing the Redis server on an unrecognized AST node.

### Confidence Score
High
