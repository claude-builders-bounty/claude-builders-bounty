#!/usr/bin/env python3
"""Prepare and optionally collect genuine Claude Code comprehension evidence.

Default: preflight only; never calls a model. Live results require semantic review against the template.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPT = """Read CLAUDE.md and the project files. Propose a concrete implementation
plan for an authenticated form that creates a note in SQLite. Include file paths,
validation, authorization, database boundary, migration filename and SQL, naming,
deployment choice, and relevant checks. Explain which project rules drive your
choices. Work with the instructions as supplied and list any assumptions.
Do not modify files or execute commands. This is a comprehension review."""

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true",
                        help="Use an already authenticated included Claude subscription.")
    parser.add_argument("--receipt", type=Path, default=ROOT / "evidence/live-preflight.json")
    parser.add_argument("--claude-command", default="npx --yes @anthropic-ai/claude-code@2.1.288")
    args = parser.parse_args()
    command = shlex.split(args.claude_command)
    if not command:
        parser.error("--claude-command cannot be empty")
    receipt = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_call_performed": False,
        "live_comprehension_confirmed": False,
        "semantic_review_required": True,
        "prompt": PROMPT,
    }

    def finish(status: str, code: int) -> int:
        receipt["status"] = status
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        print(status)
        print("Model call performed:", receipt["model_call_performed"])
        print("Live comprehension confirmed:", receipt["live_comprehension_confirmed"])
        return code

    # Refuse endpoint redirects, paid API-key routes and alternate providers.
    blocked = [k for k in os.environ if os.environ[k] and (
        k in {"ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
              "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"}
        or k.startswith("ANTHROPIC_CUSTOM_HEADERS"))]
    if blocked:
        receipt["blocked_environment_names"] = sorted(blocked)  # names only; never secrets
        return finish("BLOCKED_PROVIDER_CONFIGURATION", 2)

    with tempfile.TemporaryDirectory(prefix="claude-greenfield-") as tmp:
        project = Path(tmp) / "notes-app"
        for rel in ["app/(marketing)", "app/(app)", "app/api", "components/ui",
                    "components/feature", "lib/db/migrations", "lib/auth",
                    "lib/validation", "lib/services", "tests"]:
            (project / rel).mkdir(parents=True, exist_ok=True)
        source = (ROOT / "CLAUDE.md").read_bytes()
        shutil.copyfile(ROOT / "CLAUDE.md", project / "CLAUDE.md")
        assert (project / "CLAUDE.md").read_bytes() == source
        (project / "package.json").write_text(json.dumps({
            "name": "notes-app-comprehension-fixture", "private": True,
            "dependencies": {"next": "15.0.0", "react": "^19.0.0",
                             "better-sqlite3": "^11.0.0", "zod": "^3.0.0"},
            "scripts": {"dev": "next dev", "build": "next build",
                        "lint": "eslint .", "typecheck": "tsc --noEmit",
                        "test": "vitest run"},
        }, indent=2) + "\n")
        (project / "app/page.tsx").write_text(
            'export default function Page() { return <main>Notes</main>; }\n')
        receipt.update({
            "fresh_project_created": True,
            "fixture_dependencies_installed": False,
            "project_build_executed": False,
            "template_copied_unchanged": True,
            "template_sha256": hashlib.sha256(source).hexdigest(),
        })
        try:
            version = subprocess.run(command + ["--version"], cwd=project,
                                     text=True, capture_output=True, timeout=60)
            receipt["cli_version"] = version.stdout.strip()
            auth = subprocess.run(command + ["auth", "status"], cwd=project,
                                  text=True, capture_output=True, timeout=60)
            auth_data = json.loads(auth.stdout)
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            receipt["failure_type"] = type(exc).__name__
            return finish("BLOCKED_CLI_OR_AUTH_STATUS", 2)
        receipt["auth_status_exit_code"] = auth.returncode
        receipt["auth_status"] = {
            k: auth_data.get(k) for k in ("loggedIn", "authMethod", "subscriptionType")}
        if not auth_data.get("loggedIn"):
            return finish("BLOCKED_AUTHENTICATION", 2)
        # Console/API-key billing is outside the intended included-plan workflow.
        if str(auth_data.get("subscriptionType", "")).lower() not in {
                "pro", "max", "team", "teams", "enterprise"}:
            return finish("BLOCKED_INCLUDED_SUBSCRIPTION_UNCONFIRMED", 2)
        if not args.run_live:
            return finish("READY_FOR_EXPLICIT_LIVE_RUN", 0)

        cli_args = ["--print", PROMPT, "--restricted", "--tools", "Read,Glob,Grep",
                    "--permission-mode", "plan", "--strict-mcp-config", "--mcp-config",
                    '{"mcpServers":{}}', "--disable-slash-commands",
                    "--no-session-persistence", "--output-format", "json"]
        try:
            result = subprocess.run(command + cli_args, cwd=project,
                                    text=True, capture_output=True, timeout=240)
            receipt["live_cli_attempted"] = True
            receipt["cli_exit_code"] = result.returncode
            response = json.loads(result.stdout)
            receipt["provider_result"] = response.get("result")
            receipt["provider_is_error"] = response.get("is_error")
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            receipt["failure_type"] = type(exc).__name__
            receipt["live_cli_attempted"] = True
            return finish("LIVE_RUN_INCOMPLETE", 2)
        if result.returncode or response.get("is_error"):
            return finish("LIVE_RUN_ERROR", 2)
        receipt["model_call_performed"] = True
        # Successful CLI output is not automatically proof of comprehension.
        return finish("LIVE_RESULT_REQUIRES_COMPREHENSION_REVIEW", 0)

if __name__ == "__main__":
    raise SystemExit(main())
