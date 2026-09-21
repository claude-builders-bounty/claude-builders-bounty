# Automated Changelog Generator
import subprocess

def generate():
    result = subprocess.run(['git', 'log', '--pretty=format:%s'], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        print(f'- {line}')

if __name__ == '__main__':
    generate()
