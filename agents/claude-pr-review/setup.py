from setuptools import setup, find_packages

setup(
    name="claude-review",
    version="1.0.0",
    description="Claude Code sub-agent that reviews a PR and posts a structured comment.",
    author="Wasim",
    scripts=["claude-review"],
    install_requires=[
        "anthropic>=0.20.0",
        "requests>=2.30.0"
    ],
)
