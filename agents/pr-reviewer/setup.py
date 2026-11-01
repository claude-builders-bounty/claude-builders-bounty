from setuptools import setup, find_packages

setup(
    name="claude-review",
    version="1.0.0",
    description="Claude Code sub-agent that reviews a PR and posts a structured comment (#4)",
    author="Claude Builders Community",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.0",
    ],
    entry_points={
        "console_scripts": [
            "claude-review=claude_review.cli:main",
        ],
    },
    python_requires=">=3.8",
)
