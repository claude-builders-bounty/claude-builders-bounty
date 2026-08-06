from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "CLAUDE.md"

REQUIRED_HEADINGS = [
    "# Project instructions",
    "## Working method",
    "## Stack and versions",
    "## Directory contract",
    "## Naming and module boundaries",
    "## Development commands",
    "## Database rules",
    "## Next.js App Router rules",
    "## Server Actions, forms, and validation",
    "## UI and accessibility",
    "## Testing contract",
    "## Security and operations",
    "## What we do not do",
    "## Definition of done",
]

REQUIRED_PHRASES = [
    "Next.js 15",
    "App Router",
    "React 19",
    "TypeScript 5",
    "better-sqlite3",
    "Turso/libSQL",
    "Drizzle ORM",
    "Zod",
    "Vitest",
    "Playwright",
    "pnpm db:generate",
    "pnpm db:migrate",
    "Never use drizzle-kit push in CI or production",
    "foreign keys",
    "UTC epoch milliseconds",
    "Server Components are the default",
    "await them",
    "authorization",
    "transaction rollback",
    "httpOnly",
    "Definition of done",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    require(len(text.splitlines()) >= 180, "CLAUDE.md is unexpectedly short")

    for heading in REQUIRED_HEADINGS:
        require(heading in text, f"missing heading: {heading}")

    for phrase in REQUIRED_PHRASES:
        require(phrase in text, f"missing required rule: {phrase}")

    forbidden = [
        "TODO",
        "TBD",
        "YOUR_",
        "your-project",
        "example.com",
        "sk-",
        "BEGIN PRIVATE KEY",
    ]
    for marker in forbidden:
        require(marker not in text, f"unresolved or sensitive marker found: {marker}")

    # Every definition-of-done item must be a numbered rule, and the file must
    # contain explicit reasons/risk statements rather than generic slogans.
    done_items = re.findall(r"(?m)^\d+\. .+$", text)
    require(len(done_items) >= 7, "definition of done is incomplete")
    require(text.count("because") >= 4, "rules do not explain enough rationale")
    require(text.count("Never ") >= 8, "safety rules are incomplete")

    with tempfile.TemporaryDirectory(prefix="claude-md-greenfield-") as temp:
        fixture = Path(temp) / "next-sqlite-saas"
        fixture.mkdir()
        shutil.copy2(TEMPLATE, fixture / "CLAUDE.md")
        (fixture / "package.json").write_text(
            '{"private":true,"scripts":{"lint":"eslint .","typecheck":"tsc --noEmit",'
            '"test":"vitest run","build":"next build","db:generate":"drizzle-kit generate",'
            '"db:migrate":"drizzle-kit migrate"}}',
            encoding="utf-8",
        )
        copied = (fixture / "CLAUDE.md").read_text(encoding="utf-8")
        require(copied == text, "greenfield copy changed the instruction file")
        require((fixture / "package.json").exists(), "greenfield fixture was not created")

    print("validate_claude_md.py: PASS (structure, stack, rules, safety, and greenfield copy)")


if __name__ == "__main__":
    main()
