import subprocess
import tempfile
import os
import shutil
from pathlib import Path

def test_changelog_generation():
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"[*] Testing in temporary git repo: {temp_dir}")
        
        # 1. Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)
        
        # 2. Make initial commit
        (Path(temp_dir) / "initial.txt").write_text("initial", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "feat: initial commit with base features"], cwd=temp_dir, check=True)
        subprocess.run(["git", "tag", "v1.0.0"], cwd=temp_dir, check=True)
        
        # 3. Make subsequent commits with conventional types
        (Path(temp_dir) / "file1.txt").write_text("feature content", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "feat(auth): add OAuth2 authentication support"], cwd=temp_dir, check=True)
        
        (Path(temp_dir) / "file2.txt").write_text("bug fix", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "fix: resolve memory leak in background polling"], cwd=temp_dir, check=True)
        
        (Path(temp_dir) / "README.md").write_text("docs", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
        subprocess.run(["git", "commit", "-m", "docs: update API documentation with examples"], cwd=temp_dir, check=True)
        
        # 4. Copy generate_changelog.py into temp_dir and execute
        src_script = Path(__file__).parent / "generate_changelog.py"
        dst_script = Path(temp_dir) / "generate_changelog.py"
        shutil.copy(src_script, dst_script)
        
        res = subprocess.run(["python", "generate_changelog.py"], cwd=temp_dir, capture_output=True, text=True, check=True)
        print("[+] Execution output:\n", res.stdout)
        
        # 5. Validate CHANGELOG.md
        changelog = (Path(temp_dir) / "CHANGELOG.md").read_text(encoding="utf-8")
        print("=== GENERATED CHANGELOG.md ===")
        print(changelog)
        print("===============================")
        
        assert "### Added" in changelog
        assert "add OAuth2 authentication support" in changelog
        assert "### Fixed" in changelog
        assert "resolve memory leak in background polling" in changelog
        print("\n[OK] ALL ACCEPTANCE CRITERIA TESTS PASSED!")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_changelog_generation()
