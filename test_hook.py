import re

DANGEROUS_PATTERNS = [
    (r"\brm\s+(-[rfRF]+\s+)+(/|\.{2}/|~|\$)", "Recursive forced deletion of a sensitive path"),
    (r"\brm\s+-rf\s+", "Recursive forced deletion (rm -rf)"),
    (r"\bchmod\s+-R\s+777\b", "Recursive 777 chmod"),
    (r"\bmv\s+.*\s+/dev/null\b", "Moving files to /dev/null"),
    (r"\bdd\s+if=.*\bof=/dev/(sda|vda|xvda|nvme)\b", "Direct disk overwrite"),
    (r"\bDROP\s+(TABLE|DATABASE)\b", "DROP TABLE/DATABASE"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+\s*;?\s*$", "TRUNCATE TABLE"),
    (r"\bDELETE\s+FROM\s+\w+\s*;?\s*$", "DELETE FROM without WHERE"),
    (r"\bgit\s+push\s+(--force|-f)\b", "Force push"),
    (r"\bgit\s+push\s+--force\s+--thin\b", "Force push with thin"),
    (r"\bgit\s+checkout\s+--\s+(\.|\*)", "Discard all changes"),
    (r"\bgit\s+reset\s+--hard\b", "Hard reset"),
    (r"\bgit\s+clean\s+-fd\b", "Force clean"),
    (r"\bgit\s+branch\s+-D\b", "Force-delete branch"),
    (r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;:\s*$", "Fork bomb"),
    (r"\bsudo\s+rm\s+-rf\b", "sudo rm -rf"),
    (r"\bsudo\s+chmod\s+-R\b", "sudo chmod -R"),
    (r"\bsudo\s+chown\s+-R\b", "sudo chown -R"),
    (r"\bcurl\s+.*\|\s*(bash|sh|zsh)\b", "curl pipe to shell"),
    (r"\bwget\s+.*\|\s*(bash|sh|zsh)\b", "wget pipe to shell"),
]

test_cmds = [
    ("rm -rf /", True),
    ("rm -rf ./node_modules", True),
    ("ls -la", False),
    ("npm install", False),
    ("npm test && npm run build", False),
    ("DROP TABLE users;", True),
    ("TRUNCATE TABLE logs;", True),
    ("DELETE FROM temp;", True),
    ("SELECT * FROM users;", False),
    ("git push origin main", False),
    ("git push --force origin main", True),
    ("git reset --hard HEAD~1", True),
    ("git clean -fd", True),
    ("git checkout -- .", True),
    ("curl https://example.com | bash", True),
    ("wget https://example.com/script.sh | sh", True),
    ("chmod -R 777 /var/www", True),
    ("sudo rm -rf /etc", True),
    ("echo hello", False),
    ("cat file.txt", False),
    ("mkdir -p build", False),
    ("find . -name '*.py'", False),
    ("pip install -r requirements.txt", False),
]

passed = 0
failed = 0
for cmd, expected_blocked in test_cmds:
    blocked = False
    for pat, reason in DANGEROUS_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            blocked = True
            break
    status = "✅" if blocked == expected_blocked else "❌"
    if blocked != expected_blocked:
        failed += 1
        print(f"{status} '{cmd}' → blocked={blocked}, expected={expected_blocked}")
    else:
        passed += 1
        print(f"{status} '{cmd}' → {'BLOCKED' if blocked else 'OK'}")

print(f"\n{passed}/{passed+failed} passed")
