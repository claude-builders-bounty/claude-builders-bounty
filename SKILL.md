---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
triggers:
  - /generate-changelog
---

# Generate Changelog

When the user runs `/generate-changelog`, produce a structured `CHANGELOG.md` from the project's git history.

## Behavior

1. **Determine the range**:
   - If the user specifies a tag, use `<tag>..HEAD`.
   - If the user specifies two tags, use `<tag1>..<tag2>`.
   - Otherwise, find the most recent git tag and use `<tag>..HEAD`.
   - If no tags exist, use the full history from the first commit.

2. **Fetch commits** in the range with `git log --format="%h|%s"`.

3. **Categorize** each commit based on the conventional-commit prefix or keyword in the subject line:

   | Category     | Prefixes / Keywords                                    |
   |--------------|--------------------------------------------------------|
   | Added        | `feat`, `add`, `implement`, `introduce`, `create`, `support`, `new` |
   | Changed      | `change`, `update`, `modify`, `refactor`, `improve`, `enhance`, `rename`, `migrate`, `upgrade`, `bump`, `move`, `replace` |
   | Fixed        | `fix`, `bugfix`, `patch`, `resolve`, `close`, `repair`, `hotfix` |
   | Removed      | `remove`, `delete`, `drop`, `eliminate`, `strip`      |
   | Deprecated   | `deprecate`, `deprecated`                              |
   | Security     | `security`, `cve`, `vulnerability`, `xss`, `csrf`     |
   | Other        | anything that doesn't match the above                 |

4. **Strip** the conventional-commit prefix (e.g. `feat(scope):`) from the message before writing it to the changelog.

5. **Write** `CHANGELOG.md` in Keep-a-Changelog format:

   ```markdown
   # Changelog

   ## [version] - YYYY-MM-DD

   ### Added
   - description (abc1234)

   ### Fixed
   - description (def5678)

   ### Changed
   - ...
   ```

   If `CHANGELOG.md` already exists, **prepend** the new section above the previous entries (don't overwrite).

6. **Print a summary** showing the commit count per category.

## Usage

```
/generate-changelog            # from last tag to HEAD
/generate-changelog v1.2.0     # from v1.2.0 to HEAD
/generate-changelog v1.0.0 v2.0.0  # between two tags
```

## Notes

- The script version (`changelog.sh`) does the same thing and can be run standalone: `bash changelog.sh`.
- Both produce identical output.
