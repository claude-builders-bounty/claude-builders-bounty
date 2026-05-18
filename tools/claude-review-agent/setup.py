from setuptools import setup

setup(
    name="claude-review-agent",
    version="0.1.0",
    py_modules=["claude_review"],
    install_requires=[
        "anthropic>=0.25.0",
        "openai>=1.12.0",
    ],
    entry_points={
        "console_scripts": [
            "claude-review=claude_review:main",
        ],
    },
    author="Claude Code",
    description="AI-powered PR review agent for GitHub",
    python_requires=">=3.8",
)
