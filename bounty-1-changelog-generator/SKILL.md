# Generate Changelog

<description>
Automatically generates a structured `CHANGELOG.md` from the project's git history since the last tag.
Use this skill when the user asks to "generate a changelog", "create release notes", or when you need to summarize recent commits.
</description>

## 🛠️ Commands

This skill enables the generation of `CHANGELOG.md`.

To run it, execute the bash script provided with this skill:
```bash
bash changelog.sh
```

**How it works:**
1. Finds the last git tag using `git describe`.
2. Fetches commits since that tag (or all commits if no tags).
3. Auto-categorizes the commits into:
   - **Added**: starts with `feat`, `add`, `new`
   - **Fixed**: starts with `fix`, `bug`, `patch`
   - **Removed**: starts with `remove`, `delete`, `drop`
   - **Changed**: everything else
4. Outputs `CHANGELOG.md` in the current directory.
