#!/usr/bin/env python3
import sys
import os

REQUIRED_SECTIONS = [
    "Stack & Architecture Versions",
    "Directory Structure & Conventions",
    "Development & Build Commands",
    "Database & SQL Rules",
    "Anti-Patterns To Avoid"
]

REQUIRED_KEYWORDS = [
    "Next.js 15",
    "SQLite",
    "better-sqlite3",
    "WAL Mode",
    "Parameterized Queries",
    "use client",
    "npm run dev"
]

def validate_claude_md(filepath: str) -> dict:
    """Validates that a CLAUDE.md template contains all required production sections and rules."""
    if not os.path.exists(filepath):
        return {"success": False, "error": f"File not found: {filepath}"}

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    missing_sections = [sec for sec in REQUIRED_SECTIONS if sec not in content]
    missing_keywords = [kw for kw in REQUIRED_KEYWORDS if kw not in content]

    is_valid = len(missing_sections) == 0 and len(missing_keywords) == 0

    return {
        "success": is_valid,
        "missing_sections": missing_sections,
        "missing_keywords": missing_keywords,
        "line_count": len(content.splitlines()),
        "character_count": len(content)
    }

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "src/CLAUDE.md"
    print(f"🔍 Validating CLAUDE.md template [{filepath}]...")
    res = validate_claude_md(filepath)
    if res["success"]:
        print(f"✅ Template Validation PASSED! ({res['line_count']} lines, {res['character_count']} chars)")
    else:
        print(f"❌ Template Validation FAILED! Missing Sections: {res['missing_sections']}, Missing Keywords: {res['missing_keywords']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
