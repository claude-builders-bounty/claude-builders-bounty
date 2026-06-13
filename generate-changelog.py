import subprocess

import re

import sys

from datetime import datetime



def get_commits_since_last_tag():
  
    try:
      
        # Get the last tag
      
        last_tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], stderr=subprocess.STDOUT).decode('utf-8').strip()
      
        # Get commits since last tag

        commit_range = f"{last_tag}..HEAD"
      
    except subprocess.CalledProcessError:
      
        # No tags found, get all commits
      
        commit_range = "HEAD"
      


    cmd = ['git', 'log', commit_range, '--pretty=format:%s']
  
    commits = subprocess.check_output(cmd).decode('utf-8').split('\n')
  
    return commits
  


def categorize_commits(commits):
  
    categories = {
      
        'Added': [],
      
        'Fixed': [],
      
        'Changed': [],
      
        'Removed': [],
      
        'Other': []
      
    }
  


    patterns = {
      
        'Added': r'^(feat|add|new)',
      
        'Fixed': r'^(fix|bugfix|patch)',
      
        'Changed': r'^(refactor|upd|change|chore|docs|style|perf)',
      
        'Removed': r'^(remove|del)'
      
    }
  


    for commit in commits:
      
        if not commit:
          
            continue
          


        found = False
      
        for cat, pattern in patterns.items():
          
            if re.match(pattern, commit, re.IGNORECASE):
              
                categories[cat].append(commit)
              
                found = True
              
                break
              


        if not found:
          
            categories['Other'].append(commit)
          


    return categories
  


def generate_changelog(categories):
  
    date_str = datetime.now().strftime('%Y-%m-%d')
  
    output = [f"## [Unreleased] - {date_str}\n"]
  


    for cat in ['Added', 'Fixed', 'Changed', 'Removed', 'Other']:
      
        if categories[cat]:
          
            output.append(f"### {cat}")
          
            for commit in categories[cat]:
              
                output.append(f"- {commit}")
              
            output.append("")
          


    return "\n".join(output)
  


if __name__ == "__main__":
  
    try:
      
        commits = get_commits_since_last_tag()
      
        categories = categorize_commits(commits)
      
        changelog_content = generate_changelog(categories)
      


        with open('CHANGELOG.md', 'w') as f:
          
            f.write(changelog_content)
          


        print("CHANGELOG.md generated successfully!")
      
    except Exception as e:
      
        print(f"Error: {e}")
      
        sys.exit(1)
      


























































