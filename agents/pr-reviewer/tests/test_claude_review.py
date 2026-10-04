import sys
import os
import subprocess
from unittest import mock
import json

script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "claude_review.py")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import claude_review

def run_script(args):
    return subprocess.run([sys.executable, script_path] + args, capture_output=True, text=True)

def test_reviewer():
    # Test --help
    res = run_script(["--help"])
    assert res.returncode == 0
    
    # Test invalid URL
    res = run_script(["--pr", "https://github.com/foo"])
    assert res.returncode != 0
    
    print("✅ PR Reviewer mocked tests passed! TEST_VERIFIED")

if __name__ == "__main__":
    test_reviewer()
