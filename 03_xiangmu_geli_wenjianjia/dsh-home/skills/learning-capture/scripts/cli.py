#!/usr/bin/env python3
"""
Learning Capture - CLI Entry Point
"""

import sys
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cli.py <command> [args]")
        print("Commands:")
        print("  log        - Record a learning (correction/insight/knowledge_gap/best_practice)")
        print("  error      - Record an error")
        print("  feature    - Record a feature request")
        print("  stats      - Show learning statistics")
        print("  distill    - Run distillation (generate skill drafts)")
        print("  parse      - Parse conversation context from stdin (JSON)")
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    if cmd == "log":
        subprocess.run([sys.executable, SCRIPTS_DIR / "capture.py", "log"] + args)
    elif cmd == "error":
        subprocess.run([sys.executable, SCRIPTS_DIR / "capture.py", "error"] + args)
    elif cmd == "feature":
        subprocess.run([sys.executable, SCRIPTS_DIR / "capture.py", "feature"] + args)
    elif cmd == "stats":
        subprocess.run([sys.executable, SCRIPTS_DIR / "capture.py", "stats"])
    elif cmd == "distill":
        subprocess.run([sys.executable, SCRIPTS_DIR / "distill.py"])
    elif cmd == "parse":
        subprocess.run([sys.executable, SCRIPTS_DIR / "capture.py", "parse-context"])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()