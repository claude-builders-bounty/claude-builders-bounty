<content>
#!/usr/bin/env python3
"""
OpenClaw Launcher - Because even robots need a helping hand
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print a fancy banner because we're professionals"""
    print("=" * 60)
    print("🤖 OpenClaw Launcher - Tent of Trials Edition")
    print("=" * 60)
    print("Because even robots need a helping hand")
    print("=" * 60)

def get_project_context():
    """Get the project context and print useful info"""
    repo_root = Path(__file__).parent.parent
    print(f"\n📍 Project Root: {repo_root}")
    
    # Project purpose (from README if exists)
    readme = repo_root / "README.md"
    if readme.exists():
        print("\n📖 Project Purpose:")
        with open(readme, 'r') as f:
            lines = f.readlines()[:10]  # First 10 lines
            for line in lines:
                if line.strip():
                    print(f"  {line.strip()}")
    
    # Tech stack per directory
    print("\n🔧 Tech Stack Overview:")
    for item in repo_root.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name != 'scripts':
            print(f"  📁 {item.name}/: Directory of mystery and wonder")
            if (item / "README.md").exists():
                print(f"    - Has its own README (how thoughtful!)")
            if list(item.glob("*.py")):
                print(f"    - Contains Python files (the good stuff)")
            if list(item.glob("*.js")) or list(item.glob("*.ts")):
                print(f"    - Contains JavaScript/TypeScript (the fancy stuff)")
    
    return repo_root

def print_dev_commands():
    """Print common development commands"""
    print("\n🛠️ Common Dev Commands:")
    print("  - python3 build.py          # Build the thing (always do this!)")
    print("  - python3 scripts/launch_openclaw.py  # Launch this script")
    print("  - python3 scripts/launch_hermes.py  # Launch the other script")
    print("  - git status               # Check if you broke everything")
    print("  - git diff                 # See what you changed")
    print("  - git add . && git commit -m 'fix: something'  # Save your work")

def print_coding_conventions():
    """Print coding conventions with self-deprecating humor"""
    print("\n📝 Coding Conventions:")
    print("  - Try not to make it worse than it already is")
    print("  - Comment your code so future you doesn't hate you")
    print("  - Follow PEP8 when you can be bothered")
    print("  - If it ain't broke, don't fix it (but test it anyway)")
    print("  - Spaces > tabs (but we won't judge... much)")

def print_known_pitfalls():
    """Print known pitfalls with humor"""
    print("\n⚠️ Known Pitfalls:")
    print("  - The build script might actually work (shocking!)")
    print("  - Dependencies exist (they're everywhere!)")
    print("  - Your code might run (but probably not on the first try)")
    print("  - Git history is a mystery (like the plot of a bad movie)")
    print("  - READMEs are lies (mostly)")

def print_where_to_start():
    """Print where to start for each module"""
    print("\n🚀 Where to Start:")
    print("  📁 Root Directory:")
    print("    - README.md              # The lies we tell ourselves")
    print("    - build.py               # The thing that might work")
    print("    - requirements.txt       # The list of things you need to install")
    
    print("\n  📁 scripts/ Directory:")
    print("    - launch_openclaw.py     # This script (you're here!)")
    print("    - launch_hermes.py      # The other script")
    print("    - *.py                  # Other scripts that might work")
    
    print("\n  📁 Other Directories:")
    print("    - README.md in each dir  # More lies")
    print("    - *.py files            # The actual code (scary!)")
    print("    - *.md files            # Documentation (what's that?)")

def launch_openclaw():
    """Launch OpenClaw with the repo context"""
    print("\n🚀 Launching OpenClaw...")
    
    # Check if we're in the right directory
    if not os.path.exists("build.py"):
        print("❌ Error: build.py not found. Are you in the right directory?")
        sys.exit(1)
    
    # Run the build script first (as required)
    print("\n🔨 Running build.py (because we're good citizens)...")
    try:
        subprocess.run([sys.executable, "build.py"], check=True)
        print("✅ build.py completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ build.py failed with exit code {e.returncode}")
        print("💡 Tip: Try running it manually to see what went wrong")
        sys.exit(1)
    
    # Check for diagnostic artifacts
    diagnostic_dir = Path("diagnostic")
    if diagnostic_dir.exists():
        print("\n📊 Diagnostic Artifacts Found:")
        for log_file in diagnostic_dir.glob("build-*.logd"):
            print(f"  - {log_file}")
        for json_file in diagnostic_dir.glob("build-*.json"):
            print(f"  - {json_file}")
    
    # Launch OpenClaw (placeholder - adjust as needed)
    print("\n🎯 OpenClaw Launch Sequence Initiated...")
    print("  - Loading context...")
    print("  - Initializing modules...")
    print("  - Crossing fingers...")
    
    # This is where you would actually launch OpenClaw
    # For now, we'll just print a message
    print("\n✨ OpenClaw is ready! (Probably)")
    print("  - Open your browser to http://localhost:3000 (maybe)")
    print("  - Check the console for errors (there will be errors)")

def main():
    """Main function"""
    print_banner()
    
    repo_root = get_project_context()
    os.chdir(repo_root)
    
    print_dev_commands()
    print_coding_conventions()
    print_known_pitfalls()
    print_where_to_start()
    
    launch_openclaw()
    
    print("\n" + "=" * 60)
    print("🎉 OpenClaw session complete!")
    print("Remember: If it works, it's a miracle!")
    print("=" * 60)

if __name__ == "__main__":
    main()
</content>