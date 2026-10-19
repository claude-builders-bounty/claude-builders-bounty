from setuptools import setup, find_packages

setup(
    name="claude-review",
    version="1.0.0",
    description="Claude Code sub-agent that reviews PRs and produces structured Markdown output",
    author="Claude Builders Bounty",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "claude-review=claude_review.cli:main"
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
