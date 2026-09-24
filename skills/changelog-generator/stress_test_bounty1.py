#!/usr/bin/env python3
"""
Stress Test Suite for Bounty #1: Changelog Generator
Validates:
1. Multi-version release sequencing (v1.0.0, v1.1.0, v2.0.0) without corrupting existing history.
2. Handling conventional commit types (feat, fix, docs, chore, refactor, remove, breaking changes).
3. Non-conventional natural language commits ("Add foo", "Fix bar").
4. Zero-commit boundary case (running right after a release tag).
5. CLI wrapper (`changelog.sh`) and exit codes.
"""

import os
import sys
import shutil
import tempfile
import subprocess

def run_stress_test():
    test_dir = tempfile.mkdtemp(prefix="bounty1_stress_")
    script_path = os.path.abspath("generate_changelog.py")
    sh_wrapper = os.path.abspath("changelog.sh")

    try:
        print("[*] Initializing test Git repository...")
        subprocess.run(["git", "init"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "QA Bot"], cwd=test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "qa@example.com"], cwd=test_dir, check=True)

        # 1. Release 1 (v1.0.0)
        with open(os.path.join(test_dir, "app.py"), "w") as f:
            f.write("# v1.0.0\n")
        subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "feat: initial stable API release"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(["git", "tag", "v1.0.0"], cwd=test_dir, check=True)

        # Generate v1.0.0 changelog
        res = subprocess.run([sh_wrapper, "v1.0.0", "CHANGELOG.md"], cwd=test_dir, capture_output=True, text=True)
        assert res.returncode == 0, f"v1.0.0 generation failed: {res.stderr}"

        # 2. Release 2 (v1.1.0) with varied commit conventions
        commits = [
            ("feat(billing)!: introduce Stripe checkout integration", "stripe.py"),
            ("fix(auth): patch JWT token replay vulnerability", "auth.py"),
            ("refactor(db): migrate connection pooling to asyncpg", "db.py"),
            ("remove: delete deprecated XML serialization endpoint", "xml.py"),
            ("docs: update developer onboarding guide", "README.md"),
            ("Add webhook listener for subscription cancelation", "webhook.py"),
            ("Fix edge-case null pointer in user profile serializer", "profile.py")
        ]

        for msg, fname in commits:
            with open(os.path.join(test_dir, fname), "w") as f:
                f.write(f"# {msg}\n")
            subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
            subprocess.run(["git", "commit", "-m", msg], cwd=test_dir, check=True, capture_output=True)

        # Generate v1.1.0 changelog
        res2 = subprocess.run([sh_wrapper, "v1.1.0", "CHANGELOG.md"], cwd=test_dir, capture_output=True, text=True)
        assert res2.returncode == 0, f"v1.1.0 generation failed: {res2.stderr}"

        changelog_path = os.path.join(test_dir, "CHANGELOG.md")
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()

        print("\n=== GENERATED MULTI-RELEASE CHANGELOG ===")
        print(content)

        # Assertions
        assert "## [v1.1.0]" in content, "Missing v1.1.0 section"
        assert "## [v1.0.0]" in content, "v1.0.0 section was accidentally erased!"
        assert content.index("## [v1.1.0]") < content.index("## [v1.0.0]"), "Newer version should appear above older version!"
        
        # Verify categorizations
        v1_1_text = content.split("## [v1.0.0]")[0]
        assert "### Added" in v1_1_text
        assert "introduce Stripe checkout integration" in v1_1_text
        assert "Add webhook listener for subscription cancelation" in v1_1_text
        assert "### Fixed" in v1_1_text
        assert "patch JWT token replay vulnerability" in v1_1_text
        assert "Fix edge-case null pointer in user profile serializer" in v1_1_text
        assert "### Changed" in v1_1_text
        assert "migrate connection pooling to asyncpg" in v1_1_text
        assert "update developer onboarding guide" in v1_1_text
        assert "### Removed" in v1_1_text
        assert "delete deprecated XML serialization endpoint" in v1_1_text

        # 3. Boundary case: Zero commits since tag
        subprocess.run(["git", "tag", "v1.1.0"], cwd=test_dir, check=True)
        res3 = subprocess.run([sh_wrapper, "v1.1.1", "CHANGELOG.md"], cwd=test_dir, capture_output=True, text=True)
        assert res3.returncode == 0, f"Zero-commit generation failed: {res3.stderr}"

        with open(changelog_path, "r", encoding="utf-8") as f:
            content_after = f.read()
        assert "## [v1.1.1]" in content_after
        assert "No user-facing changes recorded" in content_after

        print("\n[✓] BOUNTY #1 PASSED ALL STRESS TESTS & REGRESSION CHECKS!")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    run_stress_test()
