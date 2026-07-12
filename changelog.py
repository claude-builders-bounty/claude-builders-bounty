import subprocess
import datetime
import re
import os
import sys

class ChangelogGenerator:
    def __init__(self, filename="CHANGELOG.md"):
        self.filename = filename
        self.categories = {
            "Added": [],
            "Fixed": [],
            "Changed": [],
            "Removed": []
        }
        self.patterns = {
            "Added": r"(feat|add|new|feature)",
            "Fixed": r"(fix|bug|patch|hotfix)",
            "Changed": r"(refactor|style|perf|chore|update|docs)",
            "Removed": r"(remove|delete|drop|cleanup)"
        }

    def run_command(self, command):
        """Executes a shell command and returns the output."""
        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            return result.strip()
        except subprocess.CalledProcessError as e:
            return None

    def get_git_info(self):
        """Fetches the last tag and commit logs."""
        last_tag = self.run_command("git describe --tags --abbrev=0")
        if last_tag is None:
            # If no tag exists, we might want to get all commits from the beginning
            git_range = "HEAD"
            version_info = "Initial Release"
        else:
            git_range = f"{last_tag}..HEAD"
            version_info = last_tag

        log_data = self.run_command(f'git log {git_range} --pretty=format:"%s"')
        return version_info, log_data

    def categorize_commits(self, commits):
        """Categorizes commits based on regex patterns."""
        for commit in commits:
            if not commit: continue
            
            matched = False
            for cat, pattern in self.patterns.items():
                if re.search(pattern, commit, re.IGNORECASE):
                    self.categories[cat].append(commit)
                    matched = True
                    break
            
            if not matched:
                self.categories["Changed"].append(commit)

    def write_to_file(self, version_info):
        """Writes the categorized commits to the CHANGELOG.md file."""
        today = datetime.date.today().strftime("%Y-%m-%d")
        file_exists = os.path.isfile(self.filename)

        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                # If new file, add the main header
                if not file_exists:
                    f.write("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")

                f.write(f"## [{today}] - {version_info}\n")
                
                for cat, entries in self.categories.items():
                    if entries:
                        f.write(f"### {cat}\n")
                        for entry in entries:
                            f.write(f"- {entry}\n")
                        f.write("\n")
                f.write("---\n\n") # Separator between versions
            
            print(f"✅ Successfully updated {self.filename}")
        except IOError as e:
            print(f"❌ Error writing to file: {e}")

    def run(self):
        """Main workflow."""
        # Check if in a git repo
        if self.run_command("git rev-parse --is-inside-work-tree") != "true":
            print("❌ Error: Not a git repository.")
            return

        version_info, log_data = self.get_git_info()

        if not log_data:
            print("ℹ️ No new commits found since the last tag.")
            return

        commits = log_data.split('\n')
        self.categorize_commits(commits)
        self.write_to_file(version_info)

if __name__ == "__main__":
    # Allows passing filename as an argument: python changelog.py my_log.md
    target_file = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    generator = ChangelogGenerator(target_file)
    generator.run()
