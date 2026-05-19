#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse

try:
    from openai import OpenAI
except ImportError:
    print("Error: The 'openai' library is required.", file=sys.stderr)
    print("Please install it using: pip install openai", file=sys.stderr)
    sys.exit(1)


def get_git_log(since="1 week ago"):
    """Extracts git commit history."""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--pretty=format:%h - %s (%an)"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching git log: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def generate_changelog(git_log, api_key):
    """Sends git log to Gemini API (via local proxy) to format as a structured CHANGELOG."""
    prompt = f"""
You are an expert technical release manager. I will provide you with a raw git commit log.
Your task is to analyze these commits and generate a clean, structured Markdown CHANGELOG.md file.

Please group the changes into standard categories (e.g., Features, Bug Fixes, Documentation, Maintenance).
Make the descriptions professional. Exclude merge commits or trivial typo fixes if they aren't important.

Here is the raw git log:
{git_log}

Output ONLY the markdown changelog, without any conversational filler.
"""
    
    # Configure the client to use our local proxy (Antigravity Manager) with Gemini models
    client = OpenAI(
        base_url="http://127.0.0.1:8045/v1",
        api_key=api_key or "sk-dummy"
    )

    try:
        response = client.chat.completions.create(
            # Using our local Gemini 3.1 Flash / Pro model
            model="gemini-3.1-flash", 
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        if response.choices:
            return response.choices[0].message.content
        else:
            print("API returned an empty response.", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md using Gemini AI.")
    parser.add_argument("--since", default="1 month ago", help="Timeframe for git log (e.g., '1 week ago', 'v1.0.0..HEAD')")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file name")
    args = parser.parse_args()

    api_key = os.environ.get("ANTIGRAVITY_MANAGER_API_KEY", "")

    print(f"Fetching git history for timescale: {args.since}...")
    git_log = get_git_log(args.since)
    
    if not git_log.strip():
        print("No commits found in the specified timeframe.")
        sys.exit(0)

    print("Sending history to Gemini AI for analysis and formatting...")
    changelog_content = generate_changelog(git_log, api_key)
    
    with open(args.output, "w", encoding="utf-8") as f:
        clean_content = changelog_content
        if clean_content.startswith("```markdown"):
            clean_content = clean_content[11:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
            
        f.write(clean_content.strip() + "\n")
        
    print(f"Success! CHANGELOG generated and saved to {args.output}")


if __name__ == "__main__":
    main()
