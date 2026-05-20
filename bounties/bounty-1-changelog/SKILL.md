# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history with automatic categorization.

## Trigger
When the user asks to generate, create, or update a changelog from git commits.

## Steps

1. Get the latest tag (if any):
   ```bash
   TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
   ```

2. Get commits since that tag:
   ```bash
   if [ -n "$TAG" ]; then
       git log --format="%s" "${TAG}..HEAD"
   else
       git log --format="%s"
   fi
   ```

3. Categorize each commit by conventional commit prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**  
   - `chore:`, `refactor:`, `perf:`, `style:`, `docs:`, `build:`, `ci:`, `test:` → **Changed**
   - `remove:`, `delete:` → **Removed**
   - Everything else → **Other**

4. Write `CHANGELOG.md` with this structure:
   ```markdown
   # Changelog
   
   ## [tag] → Unreleased — YYYY-MM-DD
   
   ### Added
   - feature description
   
   ### Fixed
   - bug fix description
   
   ### Changed
   - change description
   
   ### Removed
   - removal description
   ```

## Verification
- Run `cat CHANGELOG.md` to verify output
- Check that each commit appears in the correct category
- Verify tag filtering works if tags exist
