#!/usr/bin/env python3
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLAUDE = ROOT / "CLAUDE.md"


REQUIRED_SNIPPETS = [
    "Next.js 15 with the App Router",
    "better-sqlite3",
    "@libsql/client",
    "Folder Structure",
    "Naming Conventions",
    "SQL And Migration Conventions",
    "_migrations",
    "Component Patterns",
    "Anti-Patterns To Avoid",
    "Do not add `pages/api`",
    "npm run typecheck",
]


def main() -> None:
    text = CLAUDE.read_text()
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in text]
    assert not missing, missing

    with tempfile.TemporaryDirectory() as temp_dir:
        fixture = Path(temp_dir) / "next-sqlite-saas"
        (fixture / "app/api/health").mkdir(parents=True)
        (fixture / "db/migrations").mkdir(parents=True)
        (fixture / "db/queries").mkdir(parents=True)
        (fixture / "components/ui").mkdir(parents=True)
        (fixture / "server/actions").mkdir(parents=True)
        (fixture / "package.json").write_text(
            '{"scripts":{"dev":"next dev","build":"next build","db:migrate":"tsx db/migrate.ts"}}\n'
        )
        shutil.copy(CLAUDE, fixture / "CLAUDE.md")
        copied = (fixture / "CLAUDE.md").read_text()
        assert "If the request is ambiguous" in copied
        assert "account_id" in copied

    print("tests_ok=true")


if __name__ == "__main__":
    main()
