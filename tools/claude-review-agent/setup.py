from setuptools import setup, find_packages

setup(
    name="claude-review-agent",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["claude-review"],
    install_requires=[
        "anthropic>=0.18.0",
        "openai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "claude-review=claude-review:main",
        ],
    },
    author="Claude Code",
    description="AI-powered PR review agent for GitHub",
    python_requires=">=3.8",
)
