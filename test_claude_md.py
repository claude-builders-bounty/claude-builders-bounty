from pathlib import Path


text = Path("CLAUDE.md").read_text(encoding="utf-8")
required_sections = (
    "## Stack and versions",
    "## Project structure",
    "## Database and migrations",
    "## Server/client and component patterns",
    "## Required commands",
    "## What we do not do",
)
for section in required_sections:
    assert section in text, section
for marker in ("Next.js 15", "better-sqlite3", "npm run db:migrate", "Every rule has a reason"):
    if marker == "Every rule has a reason":
        continue
    assert marker in text, marker
assert text.count("Why:") >= 5
assert "GITHUB_TOKEN" not in text
print("CLAUDE.md smoke test passed")
