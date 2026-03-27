# path/to/existing/file.py

import git
import re

def generate_changelog():
    repo = git.Repo('.')
    last_tag = repo.tags[-1] if repo.tags else None
    commits = list(repo.iter_commits(last_tag if last_tag else 'HEAD'))

    changelog = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }

    for commit in commits:
        message = commit.message
        if re.search(r'\b(added|feat)\b', message, re.IGNORECASE):
            changelog['Added'].append(message)
        elif re.search(r'\b(fixed|fix)\b', message, re.IGNORECASE):
            changelog['Fixed'].append(message)
        elif re.search(r'\b(changed|update|improved)\b', message, re.IGNORECASE):
            changelog['Changed'].append(message)
        elif re.search(r'\b(removed|delete|deprecated)\b', message, re.IGNORECASE):
            changelog['Removed'].append(message)

    with open('CHANGELOG.md', 'w') as f:
        for category, entries in changelog.items():
            if entries:
                f.write(f'## {category}\n\n')
                for entry in entries:
                    f.write(f'- {entry}\n')
                f.write('\n')

if __name__ == "__main__":
    generate_changelog()