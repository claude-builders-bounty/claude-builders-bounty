# Generate Structured CHANGELOG from Git History

## Description
This PR implements a bash script that automatically generates a structured CHANGELOG.md from a project's git history, as requested in issue #1.

## Features
- Works via `bash changelog.sh` command
- Fetches commits since the last git tag (or all commits if no tags exist)
- Auto-categorizes commits into: Added / Fixed / Changed / Removed based on conventional commit prefixes
- Outputs properly formatted CHANGELOG.md with version sections
- Includes comprehensive README with setup instructions in 3 simple steps
- Tested with sample output included

## Acceptance Criteria Met
✅ Works via bash changelog.sh command  
✅ Fetches commits since the last git tag  
✅ Auto-categorizes into: Added / Fixed / Changed / Removed  
✅ Outputs properly formatted CHANGELOG.md  
✅ Tested on real GitHub repo (sample output included)  
✅ README with setup instructions in 3 steps or fewer  

## How to Test
1. Clone any git repository with commit history
2. Copy `changelog.sh` to the repository root
3. Make it executable: `chmod +x changelog.sh`
4. Run: `./changelog.sh`
5. View generated `CHANGELOG.md`

The script handles edge cases like repositories without tags and provides clear error messages for common issues.

## Sample Output
See `sample-CHANGELOG.md` for example output format.

Fixes #1