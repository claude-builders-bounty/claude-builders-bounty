#!/usr/bin/env python3
"""
Pre-commit hook agent for Python code quality validation.

Validates:
1. Import order (isort check)
2. Unused imports (ruff F401)
3. Type annotations on public functions
4. Docstrings on public functions

Returns non-zero exit code if any issues are found.
Can also post a comment on the PR when run in CI.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess command, capturing output."""
    return subprocess.run(cmd, capture_output=True, text=True)


def _staged_python_files() -> list[str]:
    """Return list of staged .py files (relative paths)."""
    result = _run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "*.py"])
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().splitlines() if f.endswith(".py")]


def _all_python_files() -> list[str]:
    """Return all tracked .py files in the repo."""
    result = _run(["git", "ls-files", "*.py"])
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().splitlines() if f.endswith(".py")]


# ---------------------------------------------------------------------------
# Check 1: Import order (isort)
# ---------------------------------------------------------------------------

def check_import_order(files: list[str]) -> list[str]:
    """Check import ordering with isort. Returns list of issues."""
    if not files:
        return []
    result = _run(["python", "-m", "isort", "--check-only", "--diff"] + files)
    if result.returncode != 0:
        lines = result.stdout.strip().splitlines()
        issues = []
        current_file = None
        for line in lines:
            if line.startswith("---"):
                current_file = line.split("\t")[0].replace("--- ", "").strip()
            elif line.startswith("+++"):
                continue
            elif current_file and current_file not in [i.split(":")[0] for i in issues]:
                issues.append(
                    f"{current_file}: import order needs fixing "
                    f"(run `isort {current_file}`)"
                )
        if not issues and result.stdout.strip():
            issues.append("Import order issues found (run `isort .` to fix)")
        return issues
    return []


# ---------------------------------------------------------------------------
# Check 2: Unused imports (ruff F401)
# ---------------------------------------------------------------------------

def check_unused_imports(files: list[str]) -> list[str]:
    """Check for unused imports with ruff. Returns list of issues."""
    if not files:
        return []
    result = _run(["python", "-m", "ruff", "check", "--select", "F401"] + files)
    if result.returncode != 0:
        return [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    return []


# ---------------------------------------------------------------------------
# Check 3: Type annotations on public functions
# ---------------------------------------------------------------------------

def _get_public_functions(filepath: str) -> list[tuple[str, int, bool, bool]]:
    """Parse a Python file and return (name, lineno, has_return_annotation, has_param_annotations)."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, FileNotFoundError):
        return []

    results = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip if name starts with _ (private)
            if node.name.startswith("_"):
                continue
            has_return_annotation = node.returns is not None
            # Check all params except 'self' and 'cls'
            params_without_annotation = []
            for arg in node.args.args:
                if arg.arg in ("self", "cls"):
                    continue
                if arg.annotation is None:
                    params_without_annotation.append(arg.arg)
            has_param_annotations = len(params_without_annotation) == 0
            results.append((node.name, node.lineno, has_return_annotation, has_param_annotations))

    return results


def check_type_annotations(files: list[str]) -> list[str]:
    """Check that all public functions have type annotations. Returns list of issues."""
    issues = []
    for filepath in files:
        if not Path(filepath).exists():
            continue
        funcs = _get_public_functions(filepath)
        for name, lineno, has_return, has_params in funcs:
            missing = []
            if not has_return:
                missing.append("return type")
            if not has_params:
                missing.append("parameter types")
            if missing:
                issues.append(
                    f"{filepath}:{lineno}: function '{name}' missing "
                    f"{', '.join(missing)} annotation"
                )
    return issues


# ---------------------------------------------------------------------------
# Check 4: Docstrings on public functions
# ---------------------------------------------------------------------------

def _get_public_functions_without_docstring(filepath: str) -> list[tuple[str, int]]:
    """Return (name, lineno) for public functions missing docstrings."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, FileNotFoundError):
        return []

    results = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            docstring = ast.get_docstring(node)
            if not docstring:
                results.append((node.name, node.lineno))

    return results


def check_docstrings(files: list[str]) -> list[str]:
    """Check that all public functions have docstrings. Returns list of issues."""
    issues = []
    for filepath in files:
        if not Path(filepath).exists():
            continue
        funcs = _get_public_functions_without_docstring(filepath)
        for name, lineno in funcs:
            issues.append(f"{filepath}:{lineno}: function '{name}' missing docstring")
    return issues


# ---------------------------------------------------------------------------
# PR comment posting (CI mode)
# ---------------------------------------------------------------------------

def post_pr_comment(issues: dict[str, list[str]]) -> None:
    """Post a comment on the current PR with the issues found."""
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path or not Path(event_path).exists():
        print("Not in GitHub Actions PR context; skipping PR comment.")
        return

    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return

    pr_number = event.get("pull_request", {}).get("number")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not pr_number or not repo:
        return

    total = sum(len(v) for v in issues.values())
    if total == 0:
        return

    body_lines = [
        "## Pre-commit Hook: Issues Found",
        "",
        f"The pre-commit quality check found **{total}** issue(s):",
        "",
    ]
    for check_name, check_issues in issues.items():
        if check_issues:
            body_lines.append(f"### {check_name}")
            body_lines.append("```")
            for issue in check_issues:
                body_lines.append(issue)
            body_lines.append("```")
            body_lines.append("")

    body = "\n".join(body_lines)
    _run(["gh", "pr", "comment", str(pr_number), "--repo", repo, "--body", body])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Run all checks and return exit code."""
    if os.environ.get("PRE_COMMIT_ALL_FILES"):
        files = _all_python_files()
    else:
        files = _staged_python_files()

    if not files:
        print("No Python files to check.")
        return 0

    print(f"Checking {len(files)} Python file(s): {', '.join(files)}")
    print()

    all_issues: dict[str, list[str]] = {
        "Import Order": [],
        "Unused Imports": [],
        "Type Annotations": [],
        "Docstrings": [],
    }
    exit_code = 0

    # Check 1: Import order
    print("1/4 Checking import order (isort)...")
    import_issues = check_import_order(files)
    all_issues["Import Order"] = import_issues
    if import_issues:
        print(f"  FAIL: {len(import_issues)} issue(s)")
        for issue in import_issues:
            print(f"  - {issue}")
        exit_code = 1
    else:
        print("  PASS")

    # Check 2: Unused imports
    print("2/4 Checking unused imports (ruff F401)...")
    unused_issues = check_unused_imports(files)
    all_issues["Unused Imports"] = unused_issues
    if unused_issues:
        print(f"  FAIL: {len(unused_issues)} issue(s)")
        for issue in unused_issues:
            print(f"  - {issue}")
        exit_code = 1
    else:
        print("  PASS")

    # Check 3: Type annotations
    print("3/4 Checking type annotations on public functions...")
    annotation_issues = check_type_annotations(files)
    all_issues["Type Annotations"] = annotation_issues
    if annotation_issues:
        print(f"  FAIL: {len(annotation_issues)} issue(s)")
        for issue in annotation_issues:
            print(f"  - {issue}")
        exit_code = 1
    else:
        print("  PASS")

    # Check 4: Docstrings
    print("4/4 Checking docstrings on public functions...")
    docstring_issues = check_docstrings(files)
    all_issues["Docstrings"] = docstring_issues
    if docstring_issues:
        print(f"  FAIL: {len(docstring_issues)} issue(s)")
        for issue in docstring_issues:
            print(f"  - {issue}")
        exit_code = 1
    else:
        print("  PASS")

    print()

    # Post PR comment if in CI
    if os.environ.get("CI"):
        post_pr_comment(all_issues)

    if exit_code != 0:
        print("Pre-commit check FAILED. Fix the issues above before committing.")
    else:
        print("Pre-commit check PASSED. All good!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())