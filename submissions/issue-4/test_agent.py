#!/usr/bin/env python3
"""
Test script for PR Review Agent

Run this to verify your setup before using the agent on real PRs.
"""

import os
import sys
import subprocess


def check_python_version():
    """Check Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check required Python packages"""
    try:
        import requests
        print(f"✓ requests library installed")
        return True
    except ImportError:
        print("❌ requests library not installed")
        print("   Run: pip install requests")
        return False


def check_gh_cli():
    """Check GitHub CLI is installed and authenticated"""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✓ GitHub CLI: {version}")
        else:
            print("❌ GitHub CLI not working")
            return False
        
        # Check authentication
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ GitHub CLI authenticated")
            return True
        else:
            print("⚠️  GitHub CLI not authenticated")
            print("   Run: gh auth login")
            return False
            
    except FileNotFoundError:
        print("❌ GitHub CLI not installed")
        print("   Install from: https://cli.github.com/")
        return False


def check_api_key():
    """Check Anthropic API key is set"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        # Show first/last 4 chars for verification
        masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print(f"✓ ANTHROPIC_API_KEY set ({masked})")
        return True
    else:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   Set with: export ANTHROPIC_API_KEY='your-key-here'")
        return False


def test_pr_url_parsing():
    """Test PR URL parsing"""
    print("\nTesting PR URL parsing...")
    
    # Import the module
    sys.path.insert(0, os.path.dirname(__file__))
    from pr_review_agent import parse_pr_url
    
    test_cases = [
        ("https://github.com/owner/repo/pull/123", {"owner": "owner", "repo": "repo", "pr_number": "123"}),
        ("https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4", 
         {"owner": "claude-builders-bounty", "repo": "claude-builders-bounty", "pr_number": "4"}),
    ]
    
    all_passed = True
    for url, expected in test_cases:
        try:
            result = parse_pr_url(url)
            if result == expected:
                print(f"  ✓ {url}")
            else:
                print(f"  ❌ {url}")
                print(f"     Expected: {expected}")
                print(f"     Got: {result}")
                all_passed = False
        except Exception as e:
            print(f"  ❌ {url} - {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all checks"""
    print("="*60)
    print("PR Review Agent - Setup Verification")
    print("="*60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("GitHub CLI", check_gh_cli),
        ("API Key", check_api_key),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        results.append(check_func())
    
    print("\n" + "="*60)
    
    if all(results):
        print("✅ All checks passed!")
        print("\nYou're ready to use the PR Review Agent.")
        print("\nTry a dry-run test:")
        print("  python pr_review_agent.py https://github.com/owner/repo/pull/123 --dry-run")
        return 0
    else:
        print("❌ Some checks failed")
        print("\nPlease fix the issues above before using the agent.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
