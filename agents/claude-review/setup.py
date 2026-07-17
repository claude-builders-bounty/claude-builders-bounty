"""Setup script for Claude Review Agent."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude-review",
    version="1.0.0",
    author="Claude Review Agent",
    author_email="your.email@example.com",
    description="A Claude Code sub-agent that reviews GitHub PRs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/claude-review",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "claude-review=claude_review.cli:main",
        ],
    },
)
