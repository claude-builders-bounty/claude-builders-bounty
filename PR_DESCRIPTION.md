## Summary

Implements the changelog generator requested in #1.

### What changed

- Added a dependency-free `changelog.sh` Bash script.
- Uses the latest Git tag as the changelog starting point.
- Falls back to the full Git history when no tags exist.
- Categorizes commits into Added, Changed, Fixed, and Removed.
- Supports a custom output path.
- Added isolated tests using temporary Git repositories.
- Added setup instructions and sample output.

### Testing

```bash
./tests/test_changelog.sh
```

Result:

```text
PASS: all changelog tests
```

Closes #1
