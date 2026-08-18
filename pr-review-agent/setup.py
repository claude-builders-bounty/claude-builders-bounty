from setuptools import setup, find_packages

setup(
    name="claude-review",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.34.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "claude-review=claude_review:main",
        ],
    },
    python_requires=">=3.11",
)