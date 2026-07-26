# Changelog Generator

Auto-generate `CHANGELOG.md` from git commits since the last tag, categorised into Added/Fixed/Changed/Removed.

## Setup (3 steps)

1. **Clone repo**  
   `git clone https://github.com/your-fork/claude-builders-bounty && cd claude-builders-bounty`

2. **Make executable** (already done)  
   `chmod +x changelog.py`

3. **Run**  
   `python3 changelog.py > CHANGELOG.md`  
   (or use `python changelog.py`)

## How it works

- Reads commits from the most recent tag to HEAD (or all commits if no tag exists).
- Classifies by conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.) and common keywords.
- Outputs exactly four sections: Added, Fixed, Changed, Removed.
- Zero dependencies beyond Python 3 and Git.
