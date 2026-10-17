from setuptools import setup, find_packages

setup(
    name="claude-review",
    version="1.0.0",
    description="Claude Code PR Reviewer Agent — Automated structured PR code reviews",
    author="Claude Code Community",
    py_modules=["claude_review"],
    entry_points={
        "console_scripts": [
            "claude-review=claude_review:main",
        ],
    },
    python_requires=">=3.8",
)
