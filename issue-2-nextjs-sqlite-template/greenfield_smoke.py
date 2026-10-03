from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "CLAUDE.md"

with tempfile.TemporaryDirectory() as tmp:
    project = Path(tmp) / "saas-app"
    for path in [
        "app/(marketing)",
        "app/(app)",
        "app/api",
        "components/ui",
        "components/feature",
        "lib/db/migrations",
        "lib/auth",
        "lib/validation",
        "lib/services",
        "tests",
    ]:
        (project / path).mkdir(parents=True, exist_ok=True)

    target = project / "CLAUDE.md"
    shutil.copyfile(SOURCE, target)
    text = target.read_text(encoding="utf-8")

    required = [
        "Next.js 15",
        "SQLite",
        "Server Components",
        "better-sqlite3",
        "Turso/libSQL",
        "Zod",
        "Migrations",
        "npm run dev",
        "What we do not do",
    ]
    missing = [item for item in required if item not in text]
    assert not missing, missing
    assert "<PROJECT" not in text
    assert "TODO: customize" not in text
    assert target.read_bytes() == SOURCE.read_bytes()

print("greenfield copy smoke: PASS — CLAUDE.md used unchanged")
