from pathlib import Path
text=Path(__file__).with_name("CLAUDE.md").read_text()
required=["## Stack and versions","## Folder structure","## Naming conventions","## Migration rules","## Commands","## Component patterns","## What we do not do","npm run build","better-sqlite3","Turso"]
missing=[x for x in required if x not in text]
assert not missing, missing
assert text.count("Reason:") >= 30, text.count("Reason:")
print("ok")
