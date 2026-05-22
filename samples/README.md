# Sample Review Outputs

These files are generated from real public GitHub pull requests with the deterministic validation mode:

- cli-11534-review.md: https://github.com/cli/cli/pull/11534
- cli-13482-review.md: https://github.com/cli/cli/pull/13482

Generation commands:

    node bin/claude-review.mjs --pr https://github.com/cli/cli/pull/11534 --max-files 8 --no-claude --output samples/cli-11534-review.md
    node bin/claude-review.mjs --pr https://github.com/cli/cli/pull/13482 --max-files 8 --no-claude --output samples/cli-13482-review.md
