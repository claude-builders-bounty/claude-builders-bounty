#!/usr/bin/env python3
"""
Test Suite for Changelog Generator
Creates a mock Git repository with realistic conventional commits and verifies markdown output.
"""
import os
import shutil
import tempfile
import subprocess

def test_changelog_generation():
    test_dir = tempfile.mkdtemp(prefix="test_repo_")
    script_path = os.path.abspath("generate_changelog.py")
    
    try:
        # Init git repo
        subprocess.run(["git", "init"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=test_dir, check=True)
        
        # Initial commit & tag
        with open(os.path.join(test_dir, "init.txt"), "w") as f:
            f.write("initial")
        subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(["git", "tag", "v0.9.0"], cwd=test_dir, check=True)
        
        # New feature commit
        with open(os.path.join(test_dir, "feat.txt"), "w") as f:
            f.write("feature")
        subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "feat(auth): add OAuth2 Google login flow"], cwd=test_dir, check=True, capture_output=True)
        
        # Bug fix commit
        with open(os.path.join(test_dir, "fix.txt"), "w") as f:
            f.write("fix")
        subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "fix: resolve session token expiration race condition"], cwd=test_dir, check=True, capture_output=True)
        
        # Refactor commit
        with open(os.path.join(test_dir, "refactor.txt"), "w") as f:
            f.write("refactor")
        subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "refactor(db): optimize connection pool queries"], cwd=test_dir, check=True, capture_output=True)
        
        # Remove commit
        with open(os.path.join(test_dir, "remove.txt"), "w") as f:
            f.write("remove")
        subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "remove: deprecate legacy v1 XML endpoints"], cwd=test_dir, check=True, capture_output=True)
        
        # Run changelog generator
        res = subprocess.run([sys.executable, script_path, "v1.0.0", "CHANGELOG.md"], cwd=test_dir, capture_output=True, text=True)
        assert res.returncode == 0, f"Generator failed: {res.stderr}"
        
        changelog_file = os.path.join(test_dir, "CHANGELOG.md")
        assert os.path.exists(changelog_file), "CHANGELOG.md not created"
        
        with open(changelog_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        print("=== GENERATED CHANGELOG ===")
        print(content)
        
        assert "## [v1.0.0]" in content
        assert "### Added" in content
        assert "add OAuth2 Google login flow" in content
        assert "### Fixed" in content
        assert "resolve session token expiration race condition" in content
        assert "### Changed" in content
        assert "optimize connection pool queries" in content
        assert "### Removed" in content
        assert "deprecate legacy v1 XML endpoints" in content
        
        print("\n[✓] ALL CHANGELOG GENERATOR ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    import sys
    test_changelog_generation()
