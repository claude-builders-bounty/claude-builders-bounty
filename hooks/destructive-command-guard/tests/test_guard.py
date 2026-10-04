import sys
import os
import importlib.machinery

# Load module from file with hyphens
module_name = "pre_tool_use"
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pre-tool-use")

loader = importlib.machinery.SourceFileLoader(module_name, file_path)
pre_tool_use = loader.load_module()

check_destructive = pre_tool_use.check_destructive

def test_guard():
    # Should block
    blocked, _ = check_destructive("rm -rf /tmp/x")
    assert blocked
    
    blocked, _ = check_destructive("bash -c 'rm -rf /tmp/x'")
    assert blocked
    
    blocked, _ = check_destructive("cmd1 && rm -rf /tmp/x")
    assert blocked

    # Should allow
    blocked, _ = check_destructive("echo 'rm -rf /tmp/x'")
    assert not blocked
    
    blocked, _ = check_destructive("printf 'DROP TABLE x'")
    assert not blocked
    
    blocked, _ = check_destructive("echo 'hello; DROP TABLE x'")
    assert not blocked
    
    blocked, _ = check_destructive("echo \"hello | DROP TABLE x\"")
    assert not blocked
    
    blocked, _ = check_destructive("echo 'a;b|c&&d'")
    assert not blocked
    
    blocked, _ = check_destructive("echo \\\"rm -rf /tmp\\\"")
    assert not blocked

    print("✅ All guard tests passed!")

if __name__ == "__main__":
    test_guard()
