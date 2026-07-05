#!/usr/bin/env python3
"""Greenfield smoke check for the Next.js + SQLite CLAUDE.md template."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "CLAUDE.md"

PACKAGE_JSON = {
    "name": "nextjs-sqlite-saas-smoke",
    "private": True,
    "scripts": {
        "dev": "next dev",
        "lint": "next lint",
        "typecheck": "tsc --noEmit",
        "test": "vitest run",
        "test:e2e": "playwright test",
        "db:migrate": "tsx db/migrate.ts",
        "db:reset": "tsx db/reset.ts",
        "build": "next build",
    },
}

GREENFIELD_PATHS = [
    "app/(app)/page.tsx",
    "app/actions/todos.ts",
    "components/ui/button.tsx",
    "db/client.ts",
    "db/migrations/0001_init.sql",
    "db/queries/todos.ts",
    "lib/env.ts",
    "lib/permissions.ts",
    "lib/validators/todo.ts",
    "tests/integration/todos.test.ts",
    "tests/e2e/todo-flow.spec.ts",
    ".env.example",
]

REQUIRED_BOUNDARY_SIGNALS = [
    "server action",
    "Zod",
    "permission",
    "db/migrations",
    "lib/env.ts",
    "Vitest",
    "Playwright",
]


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def script_names_from_template(text: str) -> set[str]:
    return set(re.findall(r"npm run ([a-zA-Z0-9:._-]+)", text))


def main() -> int:
    template_text = TEMPLATE.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="nextjs-sqlite-claude-smoke-") as tmp:
        project = Path(tmp)
        shutil.copyfile(TEMPLATE, project / "CLAUDE.md")
        write_file(project / "package.json", json.dumps(PACKAGE_JSON, indent=2) + "\n")
        for relative_path in GREENFIELD_PATHS:
            write_file(project / relative_path)

        copied_template = (project / "CLAUDE.md").read_text(encoding="utf-8")
        if copied_template != template_text:
            raise AssertionError("Copied CLAUDE.md does not match the source template.")

        package_scripts = PACKAGE_JSON["scripts"]
        missing_scripts = sorted(script_names_from_template(template_text) - set(package_scripts))
        if missing_scripts:
            raise AssertionError(f"Template references package scripts missing from smoke package.json: {missing_scripts}")

        missing_paths = [path for path in GREENFIELD_PATHS if not (project / path).exists()]
        if missing_paths:
            raise AssertionError(f"Smoke project is missing expected paths: {missing_paths}")

        missing_signals = [signal for signal in REQUIRED_BOUNDARY_SIGNALS if signal not in template_text]
        if missing_signals:
            raise AssertionError(f"Template is missing boundary signals: {missing_signals}")

    print("Greenfield smoke check passed.")
    print(f"Copied CLAUDE.md into a temporary project and verified {len(GREENFIELD_PATHS)} expected paths.")
    print(f"Checked {len(script_names_from_template(template_text))} npm scripts against package.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
